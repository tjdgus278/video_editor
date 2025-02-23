from PIL import Image, ImageDraw, ImageFont
import numpy as np
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import os
from moviepy.editor import ImageClip, CompositeVideoClip, AudioFileClip, CompositeAudioClip
from gtts import gTTS

app = Flask(__name__)
CORS(app)

# 저장 폴더 설정
IMAGE_FOLDER = "uploaded_images"
OUTPUT_FOLDER = "output_videos"
TTS_FOLDER = "tts_audio"
BGM_FOLDER = "bgm_audio"

os.makedirs(IMAGE_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)
os.makedirs(TTS_FOLDER, exist_ok=True)
os.makedirs(BGM_FOLDER, exist_ok=True)

def render_text_clip(txt, fontsize, font_path, color, duration, clip_size):
    """ 텍스트를 이미지로 그리고, 해당 이미지를 비디오 클립으로 반환하는 함수 """
    img = Image.new("RGBA", clip_size, (0, 0, 0, 0))  # 투명 배경
    draw = ImageDraw.Draw(img)  
    
    try:
        font = ImageFont.truetype(font_path, fontsize)
    except Exception as e:
        # 기본 폰트 사용
        font = ImageFont.load_default()

    # 텍스트의 bounding box 계산
    bbox = draw.textbbox((0, 0), txt, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    
    # 텍스트를 중앙에 배치
    position = ((clip_size[0] - text_width) // 2, (clip_size[1] - text_height) // 2)
    
    # 텍스트 그리기
    draw.text(position, txt, font=font, fill=color)
    
    # 이미지 배열로 변환 후 ImageClip 생성
    img_array = np.array(img)
    clip = ImageClip(img_array).set_duration(duration)
    
    return clip

font_map = {
    "NanumBarunpenB": "custom_fonts/NanumBarunpenB.ttf",
    "NanumBrush": "custom_fonts/NanumBrush.ttf",
    "NanumGothic": "custom_fonts/NanumGothic.ttf",
    "NanumGothicBold": "custom_fonts/NanumGothicBold.ttf",
    "잘난체TTF": "custom_fonts/잘난체TTF.ttf"
}

def generate_tts(text, index):
    """TTS 음성 생성"""
    if not text:
        return None
    tts_path = os.path.join(TTS_FOLDER, f"tts_{index}.mp3")
    try:
        tts = gTTS(text=text, lang="ko")
        tts.save(tts_path)
        return tts_path
    except Exception as e:
        print(f"Error generating TTS: {e}")
        return None

@app.route('/generate-video', methods=['POST'])
def generate_video():
    try:
        # FormData로 받은 데이터 처리
        images = request.files.getlist('images')
        durations = request.form.getlist('durations[]')
        animations = request.form.getlist('animations[]')
        title_text = request.form.get('topicText', None)
        title_font_size = int(request.form.get('titleFontSize'))
        script_font_size = int(request.form.get('scriptFontSize'))
        selected_font_name = request.form.get('selectedFont')
        selected_font_path = font_map.get(selected_font_name)  # 기본값 설정
        scripts = request.form.getlist('scripts[]')
        use_tts = request.form.getlist('ttsEnabled[]')
        bgm = request.files.get('bgm', None)
        output_path = os.path.join(OUTPUT_FOLDER, "output.mp4")

        # 로그 출력
        print("=== Received Data ===")
        print(f"Images: {[img.filename for img in images]}")
        print(f"Durations: {durations}")
        print(f"Animations: {animations}")
        print(f"Title Text: {title_text}")
        print(f"Title Font Size: {title_font_size}")
        print(f"Script Font Size: {script_font_size}")
        print(f"Selected Font Name: {selected_font_name}")
        print(f"Selected Font Path: {selected_font_path}")
        print(f"Scripts: {scripts}")
        print(f"TTS Enabled: {use_tts}")
        print(f"BGM: {bgm.filename if bgm else 'No BGM'}")
        print(f"Output Path: {output_path}")
        print("=====================")

        if len(images) != len(durations) or len(images) != len(animations) or len(images) != len(scripts) or len(images) != len(use_tts):
            return jsonify({"error": "Mismatch between the number of images and the data arrays (durations, animations, scripts, ttsEnabled)"}), 400

        if not images:
            return jsonify({"error": "No images provided"}), 400

        clips = []
        audio_clips = []
        current_time = 0

        # 받은 이미지 파일 처리
        for i, image in enumerate(images):
            local_image = os.path.join(IMAGE_FOLDER, f"image_{i}.jpg")
            image.save(local_image)  # 이미지 저장

            duration = float(durations[i]) if durations else 3
            if title_text:
                title_clip = render_text_clip(
                    txt=title_text,
                    fontsize=title_font_size,
                    font_path=selected_font_path,
                    color="white",
                    duration=duration,
                    clip_size=(1080, 300)
                )
                title_clip = title_clip.set_position(('center', 200))
                title_clip = title_clip.set_start(current_time)
                title_clip = title_clip.set_end(current_time + duration)
            else:
                title_clip = None

            clip = animate_image(image, duration, animations[i])
            clip = clip.set_start(current_time)
            clip = clip.set_end(current_time + duration)

            if scripts[i]:
                script_clip = render_text_clip(
                    txt=scripts[i],
                    fontsize=script_font_size,
                    font_path=selected_font_path,
                    color="white",
                    duration=duration,
                    clip_size=(1080, 150)
                )
                script_clip = script_clip.set_position(('center', 1400))
                script_clip = script_clip.set_start(current_time)
                script_clip = script_clip.set_end(current_time + duration)

            clips.append(clip)
            if title_clip:
                clips.append(title_clip)
            if script_clip:
                clips.append(script_clip)

            # TTS 처리
            if use_tts[i] == 'true':
                tts_audio_path = generate_tts(scripts[i], i)
                if tts_audio_path:
                    tts_audio = AudioFileClip(tts_audio_path)
                    tts_audio = tts_audio.set_start(current_time)
                    if tts_audio.duration > clip.duration:
                        # 오디오 길이가 비디오보다 짧으면 오디오를 반복하지 않고, 끝에 맞춰서 자름
                        tts_audio = tts_audio.subclip(current_time, clip.duration)
                    audio_clips.append(tts_audio)

            current_time += duration

        # 비디오 클립 합치기
        final_clip = CompositeVideoClip(clips, size=(1080, 1920))

        # 배경 음악 처리
        if bgm:
            bgm_path = os.path.join(BGM_FOLDER, "bgm.mp3")
            bgm.save(bgm_path)
            bgm_audio = AudioFileClip(bgm_path).set_duration(final_clip.duration)
            audio_clips.append(bgm_audio.volumex(0.3))

        # 오디오가 있다면 비디오에 오디오 추가
        if audio_clips:
            final_audio = CompositeAudioClip(audio_clips)
            final_clip = final_clip.set_audio(final_audio)

        # 최종 비디오 저장
        final_clip.write_videofile(output_path, codec="libx264", fps=24)
        return jsonify({"video_url": f"http://localhost:5000/get-video?filename=output.mp4"}), 200
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": str(e)}), 500

def animate_image(image, duration, effect):
    # 이미지를 PIL로 열고, numpy 배열로 변환
    pil_image = Image.open(image)
    img_array = np.array(pil_image)

    clip = ImageClip(img_array, duration=duration)
    final_width, final_height = 1080, 1920

    clip = clip.resize(width=final_width)
    w, h = clip.size
    clip = clip.crop(x_center=clip.w / 2, y_center=clip.h / 2, width=1080, height=3840)
    clip = clip.set_position("center")

    if effect == "stop":
        return clip.resize(lambda t: 1 + 0.5 * (t / duration))
    elif effect == "slide-left":
        return clip.set_position(lambda t: (-(w - final_width) / 2 - 100 * (t / duration), "center"))
    elif effect == "slide-right":
        return clip.set_position(lambda t: ((w - final_width) / 2 + 100 * (t / duration), "center"))
    elif effect == "slide-up":
        return clip.set_position(lambda t: ("center", -(h - final_height) / 2 - 100 * (t / duration)))
    elif effect == "slide-down":
        return clip.set_position(lambda t: ("center", -(h - final_height) / 2 + 100 * (t / duration)))
    return clip

@app.route('/get-video', methods=['GET'])
def get_video():
    filename = request.args.get('filename')
    file_path = os.path.join(OUTPUT_FOLDER, filename)
    if os.path.exists(file_path):
        print(f"File path: {file_path}")
        return send_file(file_path, mimetype='video/mp4')
    return jsonify({"error": "File not found"}), 404

if __name__ == '__main__':
    app.run(debug=True)
