
from pathlib import Path
import json, os, subprocess, shutil
import numpy as np
import cv2
from pypdf import PdfReader
import fitz

TEAM = "테스트어린이집"
GOOD_PDF = f"{TEAM}_숏폼공모서류.pdf"
GOOD_VIDEO = f"{TEAM}_숏폼영상.MP4"

SOURCE_RULES = {
    "R05":"제출목록: ① 제출서류와 ② 영상작품 제출",
    "R06":"제출목록: ① 제출서류와 ② 영상작품 제출",
    "R07":"아래 서류 일체를 하나의 PDF 파일로 변환하여 제출",
    "R08":"제출서류 파일명: 어린이집명_숏폼공모서류.pdf",
    "R09":"붙임1. 참가 신청서 및 개인정보 수집·이용 동의서",
    "R10":"붙임2. 초상권 사용 동의서",
    "R11":"붙임3. 출품 영상작품 설명서",
    "R12":"영상작품 파일명: 어린이집명_숏폼영상.MP4",
    "R13":"영상길이: 30초~60초 이내",
    "R14":"영상해상도: 1080×1920 픽셀 이상(FHD)",
    "R15":"영상비율: 세로형 영상 9:16",
    "R16":"파일형식: MP4",
    "R17":"파일크기: 최대 300MB",
    "R19":"사진으로만 제작한 영상은 심사에서 제외",
    "R20":"영상에 사용된 소스(음악, 이미지, 폰트 등)는 저작권 문제가 없는 무료 소스 또는 라이선스를 확보한 것이어야 함",
    "R21":"생성형 AI만을 활용하여 제작한 영상(AI 생성 영상물)은 제출할 수 없음",
}

CONCEPT_TOKENS = {
    "application": ["참가","신청서"],
    "privacy": ["개인정보","수집","이용","동의서"],
    "portrait": ["초상권","사용","동의서"],
    "description": ["출품","영상","작품","설명서"],
}

def ffprobe(path: Path):
    p = subprocess.run([
        "ffprobe","-v","error","-show_entries",
        "format=duration,format_name,size:stream=codec_type,width,height",
        "-of","json",str(path)
    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if p.returncode != 0:
        return {"error":p.stderr.strip()}
    return json.loads(p.stdout)

def pdf_text(path: Path):
    try:
        reader=PdfReader(str(path))
        return "\n".join((p.extract_text() or "") for p in reader.pages)
    except Exception:
        return ""

def normalize(s):
    # punctuation/spacing-insensitive; semantics still handled by token sets below.
    for ch in [" ","\n","\t","·","ㆍ","•","-","_","(",")","[","]",":","/"]:
        s=s.replace(ch,"")
    return s

def contains_concept(text, token_list):
    t=normalize(text)
    return all(normalize(tok) in t for tok in token_list)

def finding(rule_id,status,message,details=None):
    return {
        "requirement_id":rule_id,
        "status":status,
        "message":message,
        "details":details or {},
        "evidence_quote":SOURCE_RULES[rule_id]
    }

def render_pdf_for_vision(pdf_path: Path, out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)
    paths=[]
    doc=fitz.open(pdf_path)
    for i,p in enumerate(doc):
        pix=p.get_pixmap(matrix=fitz.Matrix(1.6,1.6),alpha=False)
        out=out_dir/f"page_{i+1}.png"
        pix.save(str(out))
        paths.append(str(out))
    doc.close()
    return paths

def classify_photo_only(path: Path):
    """
    v1.4 R19 classifier — GLOBAL MOTION + RESIDUAL LOCAL MOTION.

    Policy:
    - PHOTO_ONLY: clear static / hard-cut / crossfade slideshow evidence.
    - REVIEW: sustained motion is mostly explainable by one global affine
      transform (Ken Burns / pan / zoom-like), so file-only proof is ambiguous.
    - MOTION_VIDEO: residual local/non-rigid motion remains after global
      affine compensation.

    Frozen development thresholds were selected ONLY from already-known
    v1.1-v1.3 development/failure cases, before the v1.4 holdout is created.

    Pair analysis:
    - sample ~2 fps, resize to 240 px height, grayscale
    - scene cut: MAD > 30 OR gray histogram correlation < 0.45
    - estimate global affine from tracked corners + RANSAC
    - global-only pair:
        affine inlier ratio >= .90,
        nontrivial transform magnitude >= .20,
        and residual is not extremely large
    - local-motion pair:
        after excluding a strong global-only explanation,
        residual supports localized/non-rigid change:
        (frac(|residual|>12) >= .007 and p99 >= 15) OR
        (frac(|residual|>8) >= .02 and p95 >= 5) OR
        residual mean >= 3

    Video decision:
    - MOTION_VIDEO if local-motion fraction >= .20
    - REVIEW if global-only fraction >= .15 and local-motion fraction < .20
    - REVIEW if small residual/local evidence exists but does not reach PASS
    - otherwise PHOTO_ONLY
    """
    cap=cv2.VideoCapture(str(path))
    fps=cap.get(cv2.CAP_PROP_FPS) or 30.0
    step=max(1,int(round(fps/2.0)))
    frames=[]
    idx=0
    while True:
        ok,fr=cap.read()
        if not ok:
            break
        if idx % step == 0:
            h,w=fr.shape[:2]
            target_h=240
            target_w=max(64,int(round(w*target_h/h)))
            fr=cv2.resize(fr,(target_w,target_h),interpolation=cv2.INTER_AREA)
            frames.append(cv2.cvtColor(fr,cv2.COLOR_BGR2GRAY))
        idx+=1
    cap.release()

    if len(frames)<5:
        return {"classification":"REVIEW","reason":"too_few_sampled_frames","sampled_frames":len(frames)}

    local_pairs=[]
    global_pairs=[]
    static_pairs=[]
    scene_cuts=0

    for a,b in zip(frames[:-1],frames[1:]):
        mad=float(np.mean(cv2.absdiff(a,b)))
        ha=cv2.calcHist([a],[0],None,[32],[0,256])
        hb=cv2.calcHist([b],[0],None,[32],[0,256])
        cv2.normalize(ha,ha); cv2.normalize(hb,hb)
        hist_corr=float(cv2.compareHist(ha,hb,cv2.HISTCMP_CORREL))
        if mad>30.0 or hist_corr<0.45:
            scene_cuts+=1
            continue

        pts=cv2.goodFeaturesToTrack(a,maxCorners=250,qualityLevel=0.005,minDistance=4,blockSize=5)
        M=None
        inlier_ratio=0.0
        if pts is not None and len(pts)>=5:
            pts2,st,_=cv2.calcOpticalFlowPyrLK(
                a,b,pts,None,winSize=(21,21),maxLevel=3,
                criteria=(cv2.TERM_CRITERIA_EPS|cv2.TERM_CRITERIA_COUNT,30,0.01)
            )
            if pts2 is not None and st is not None:
                good1=pts[st.flatten()==1].reshape(-1,2)
                good2=pts2[st.flatten()==1].reshape(-1,2)
                if len(good1)>=5:
                    M,inliers=cv2.estimateAffinePartial2D(
                        good1,good2,method=cv2.RANSAC,
                        ransacReprojThreshold=2.0,maxIters=1000,
                        confidence=0.99,refineIters=10
                    )
                    if inliers is not None and len(inliers):
                        inlier_ratio=float(np.mean(inliers))

        h,w=a.shape
        global_mag=0.0
        if M is not None:
            warped=cv2.warpAffine(a,M,(w,h),flags=cv2.INTER_LINEAR,
                                  borderMode=cv2.BORDER_CONSTANT,borderValue=0)
            mask=cv2.warpAffine(
                np.ones_like(a,dtype=np.uint8)*255,M,(w,h),
                flags=cv2.INTER_NEAREST,borderMode=cv2.BORDER_CONSTANT,borderValue=0
            )>0
            mask=cv2.erode(mask.astype(np.uint8),np.ones((5,5),np.uint8),iterations=1).astype(bool)
            vals=cv2.absdiff(warped,b)[mask]
            if vals.size==0:
                vals=cv2.absdiff(a,b).ravel()

            a11,a12,tx=M[0]
            a21,a22,ty=M[1]
            scale=float(np.sqrt(a11*a11+a21*a21))
            angle=float(np.degrees(np.arctan2(a21,a11)))
            trans=float(np.sqrt(tx*tx+ty*ty))
            global_mag=trans + abs(scale-1.0)*50.0 + abs(angle)*0.5
        else:
            vals=cv2.absdiff(a,b).ravel()

        residual_mean=float(np.mean(vals))
        p95=float(np.percentile(vals,95))
        p99=float(np.percentile(vals,99))
        frac8=float(np.mean(vals>8))
        frac12=float(np.mean(vals>12))

        residual_signal=(
            (frac12>=0.007 and p99>=15.0) or
            (frac8>=0.02 and p95>=5.0) or
            residual_mean>=3.0
        )

        strong_global=(
            M is not None and
            inlier_ratio>=0.90 and
            global_mag>=0.20 and
            frac12<0.10
        )

        local_motion=bool(residual_signal and not strong_global)
        global_only=bool(strong_global and not local_motion)
        static=bool(not local_motion and not global_only)

        local_pairs.append(local_motion)
        global_pairs.append(global_only)
        static_pairs.append(static)

    noncut=len(local_pairs)
    if noncut==0:
        return {
            "classification":"PHOTO_ONLY",
            "reason":"all_pairs_are_scene_cuts",
            "sampled_frames":len(frames),
            "scene_cuts":scene_cuts
        }

    lf=float(np.mean(local_pairs))
    gf=float(np.mean(global_pairs))
    sf=float(np.mean(static_pairs))

    if lf>=0.20:
        classification="MOTION_VIDEO"
    elif gf>=0.15 and lf<0.20:
        classification="REVIEW"
    elif lf>0.0:
        classification="REVIEW"
    else:
        classification="PHOTO_ONLY"

    return {
        "classification":classification,
        "sampled_frames":len(frames),
        "scene_cuts":scene_cuts,
        "noncut_pairs":noncut,
        "local_motion_fraction":round(lf,4),
        "global_only_fraction":round(gf,4),
        "static_fraction":round(sf,4),
        "policy":{
            "motion_pass_local_fraction":0.20,
            "global_review_fraction":0.15
        }
    }

def validate_case(case_dir: Path):
    findings=[]
    files=[p for p in case_dir.iterdir() if p.is_file()]
    pdfs=[p for p in files if p.suffix.lower()==".pdf"]
    videos=[p for p in files if p.suffix.lower() in {".mp4",".mov",".avi",".mkv"}]

    if not pdfs:
        findings.append(finding("R05","BLOCKER","제출서류 PDF가 없습니다."))
    if not videos:
        findings.append(finding("R06","BLOCKER","영상작품 파일이 없습니다."))

    if len(pdfs)!=1:
        findings.append(finding("R07","BLOCKER",f"제출서류는 하나의 PDF여야 하나 {len(pdfs)}개가 있습니다.",{"pdf_count":len(pdfs)}))
    if not (case_dir/GOOD_PDF).exists():
        findings.append(finding("R08","REVIEW","제출서류 파일명이 지정 형식과 다릅니다.",{"expected":GOOD_PDF}))

    if pdfs:
        combined="\n".join(pdf_text(p) for p in pdfs)
        norm=normalize(combined)
        if len(norm)<40:
            vision_dir=case_dir/"_vision_pages"
            pages=[]
            for p in pdfs:
                pages += render_pdf_for_vision(p, vision_dir/p.stem)
            for rid,concept,label in [
                ("R09","application","참가 신청서"),
                ("R09","privacy","개인정보 수집·이용 동의서"),
                ("R10","portrait","초상권 사용 동의서"),
                ("R11","description","출품 영상작품 설명서"),
            ]:
                findings.append(finding(rid,"VISION_PENDING",
                    f"이미지형 PDF라 {label} 존재 여부를 vision fallback으로 판정해야 합니다.",
                    {"concept":concept,"vision_pages":pages}))
        else:
            if not contains_concept(combined,CONCEPT_TOKENS["application"]):
                findings.append(finding("R09","BLOCKER","참가 신청서가 확인되지 않습니다."))
            if not contains_concept(combined,CONCEPT_TOKENS["privacy"]):
                findings.append(finding("R09","BLOCKER","개인정보 수집·이용 동의서가 확인되지 않습니다."))
            if not contains_concept(combined,CONCEPT_TOKENS["portrait"]):
                findings.append(finding("R10","BLOCKER","초상권 사용 동의서가 확인되지 않습니다."))
            if not contains_concept(combined,CONCEPT_TOKENS["description"]):
                findings.append(finding("R11","BLOCKER","출품 영상작품 설명서가 확인되지 않습니다."))

    vp=case_dir/GOOD_VIDEO
    if not vp.exists():
        findings.append(finding("R12","BLOCKER","영상작품 파일명이 지정 형식과 다릅니다.",{"expected":GOOD_VIDEO}))
        if videos:
            vp=videos[0]

    if vp.exists():
        info=ffprobe(vp)
        if "error" in info:
            findings.append(finding("R16","BLOCKER","영상 파일을 MP4로 정상 판독할 수 없습니다.",{"error":info["error"]}))
        else:
            fmt=info.get("format",{})
            streams=[s for s in info.get("streams",[]) if s.get("codec_type")=="video"]
            s=streams[0] if streams else {}
            dur=float(fmt.get("duration") or 0)
            w=int(s.get("width") or 0); h=int(s.get("height") or 0)
            if dur<30 or dur>60:
                findings.append(finding("R13","BLOCKER","영상 길이가 30~60초 범위를 벗어납니다.",{"duration_seconds":dur}))
            if w<1080 or h<1920:
                findings.append(finding("R14","BLOCKER","영상 해상도가 1080×1920 이상이 아닙니다.",{"width":w,"height":h}))
            ratio=(w/h) if h else 0
            if h and abs(ratio-(9/16))/(9/16)>0.005:
                findings.append(finding("R15","BLOCKER","영상 비율이 9:16이 아닙니다.",{"width":w,"height":h,"ratio":ratio}))
            fmtname=fmt.get("format_name","")
            if "mp4" not in fmtname and "mov" not in fmtname:
                findings.append(finding("R16","BLOCKER","영상 내부 컨테이너가 MP4 계열이 아닙니다.",{"format_name":fmtname}))
            if vp.stat().st_size>300*1024*1024:
                findings.append(finding("R17","BLOCKER","영상 파일이 300MB를 초과합니다.",{"bytes":vp.stat().st_size}))

            po=classify_photo_only(vp)
            # v1.5 safety policy: R19 can NEVER auto-BLOCK.
            # Any non-confident/negative content classification becomes REVIEW.
            # Only confident MOTION_VIDEO produces no R19 finding.
            if po.get("classification")=="PHOTO_ONLY":
                findings.append(finding(
                    "R19","REVIEW",
                    "사진-only/슬라이드쇼 가능성이 감지되었습니다. 공고상 심사 제외 대상일 수 있어 직접 확인이 필요합니다.",
                    {**po,"policy":"R19_REVIEW_ONLY"}
                ))
            elif po.get("classification")=="REVIEW":
                findings.append(finding(
                    "R19","REVIEW",
                    "전역 pan/zoom 또는 애매한 motion 패턴이라 photo-only 여부를 직접 확인해야 합니다.",
                    {**po,"policy":"R19_REVIEW_ONLY"}
                ))
            elif po.get("classification")=="UNKNOWN":
                findings.append(finding(
                    "R19","REVIEW",
                    "photo-only 여부를 자동 판정하지 못했습니다.",
                    {**po,"policy":"R19_REVIEW_ONLY"}
                ))

        findings.append(finding("R20","REVIEW","외부 소스 라이선스 보유 여부는 제출 파일만으로 확정할 수 없습니다.",{"automatic_verification":"UNAVAILABLE"}))
        findings.append(finding("R21","REVIEW","생성형 AI만으로 제작됐는지는 제출 파일만으로 신뢰성 있게 확정할 수 없습니다.",{"automatic_verification":"UNAVAILABLE"}))

    blockers=sorted(set(f["requirement_id"] for f in findings if f["status"]=="BLOCKER"))
    reviews=sorted(set(f["requirement_id"] for f in findings if f["status"]=="REVIEW"))
    vision_pending=[f for f in findings if f["status"]=="VISION_PENDING"]
    return {
        "case_id":case_dir.name,
        "findings":findings,
        "blocker_rule_ids":blockers,
        "review_rule_ids":reviews,
        "vision_pending":vision_pending
    }

if __name__=="__main__":
    import sys
    print(json.dumps(validate_case(Path(sys.argv[1])),ensure_ascii=False,indent=2))
