import cv2
import os
from tqdm import tqdm
from config import VIDEO_DIR, FRAME_DIR

def extract_frames(video_path, save_dir, num_frames=10):

    cap = cv2.VideoCapture(video_path)

    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    interval = max(total // num_frames,1)

    count = 0
    saved = 0

    while True:

        ret, frame = cap.read()

        if not ret:
            break

        if count % interval == 0 and saved < num_frames:

            frame_path = os.path.join(save_dir,f"{saved}.jpg")

            cv2.imwrite(frame_path, frame)

            saved += 1

        count += 1

    cap.release()


def process_dataset():

    os.makedirs(FRAME_DIR,exist_ok=True)

    videos = os.listdir(VIDEO_DIR)

    for video in tqdm(videos):

        video_path = os.path.join(VIDEO_DIR,video)

        video_id = video.split(".")[0]

        save_dir = os.path.join(FRAME_DIR,video_id)

        os.makedirs(save_dir,exist_ok=True)

        extract_frames(video_path,save_dir)


if __name__ == "__main__":

    process_dataset()