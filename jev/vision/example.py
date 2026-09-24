"""Run from any cwd: python /model/vision/example.py --model-dir /model --image image.png --request question.json"""
import argparse
import json
from pathlib import Path
from PIL import Image
from predictor import VisionDecisionEngine

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--model-dir',required=True)
    p.add_argument('--image',required=True)
    p.add_argument('--request',required=True)
    p.add_argument('--device',default='cuda')
    a=p.parse_args()
    engine=VisionDecisionEngine(a.model_dir,a.device)
    with Image.open(a.image) as image:
        result=engine.predict(json.loads(Path(a.request).read_text()),image)
    print(json.dumps(result,ensure_ascii=False,indent=2))

if __name__=='__main__':main()
