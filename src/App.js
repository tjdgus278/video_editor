import React, { useState } from 'react';
import { useDropzone } from 'react-dropzone';
import './App.css';

const App = () => {
  const [images, setImages] = useState([]);
  const [topicText, setTopicText] = useState('');
  const [scripts, setScripts] = useState({});
  const [durations, setDurations] = useState({});
  const [animations, setAnimations] = useState({});
  const [bgm, setBgm] = useState(null);
  const [ttsEnabled, setTtsEnabled] = useState({});
  const [titleFontSize, setTitleFontSize] = useState(200);  // 제목 폰트 크기
  const [scriptFontSize, setScriptFontSize] = useState(100);  // 스크립트 폰트 크기
  const [selectedFont, setSelectedFont] = useState('NanumGothic');  // 기본 폰트
  const [isLoading, setIsLoading] = useState(false);
  const [videoUrl, setVideoUrl] = useState(null);  // 비디오 URL 상태 추가

  const handleClick = async () => {
    setIsLoading(true);  // 로딩 시작
    await handleGenerateVideo();  // 비디오 생성 함수 호출
    setIsLoading(false);  // 로딩 끝
  };

  const handleDownload = () => {
    if (videoUrl) {
      // 서버에서 반환된 URL로 바로 다운로드 링크를 생성
      const link = document.createElement('a');
      link.href = videoUrl;  // 비디오 URL을 사용
      link.download = 'generated_video.mp4';  // 다운로드될 파일 이름
      link.click();
    } else {
      alert('비디오가 아직 생성되지 않았습니다.');
    }
  };

  const handleGenerateVideo = async () => {
    const formData = new FormData();

    // 이미지를 포함하여 각 항목을 추가
    images.forEach((image, index) => {
      formData.append('images', image.file);
      formData.append(`durations[]`, durations[index] || 5);  // 기본값 5
      formData.append(`animations[]`, animations[index] || 'zoom');  // 기본값 'zoom'
      formData.append(`scripts[]`, scripts[index] || '');  // 기본값 빈 문자열
      formData.append(`ttsEnabled[]`, ttsEnabled[index] ? 'true' : 'false');  // true/false 값
    });

    formData.append('topicText', topicText);
    if (bgm) formData.append('bgm', bgm);

    formData.append('titleFontSize', titleFontSize);  // 예시로 60을 설정
    formData.append('scriptFontSize', scriptFontSize); // 예시로 40을 설정
    formData.append('selectedFont', selectedFont); // 예시로 폰트 경로 설정

    try {
      const response = await fetch('http://127.0.0.1:5000/generate-video', {
        method: 'POST',
        body: formData,
      });

      if (response.ok) {
        const data = await response.json();
        const videoUrl = data.video_url;
        console.log("Generated video URL:", videoUrl);

        // 비디오 URL이 존재하면 상태에 저장
        if (videoUrl) {
          setVideoUrl(videoUrl);  // videoUrl 상태에 URL 저장
          alert('Video generation successful!');
        } else {
          alert('Failed to generate video URL');
        }
      } else {
        const result = await response.json();
        alert(`Error: ${result.error}`);
      }
    } catch (error) {
      alert('Error generating video');
      console.error(error);
    }
  };

  const onDrop = (acceptedFiles) => {
    setImages((prev) => [...prev, ...acceptedFiles.map((file) => ({ file, preview: URL.createObjectURL(file) }))]);
  };

  const { getRootProps, getInputProps } = useDropzone({ onDrop, accept: 'image/*', multiple: true });

  const handleChange = (setter) => (index) => (event) => {
    setter((prev) => ({ ...prev, [index]: event.target.value }));
  };

  return (
    <div className="App">
      <div className="title-container">
        <h1>Shorts Maker</h1>

        <button onClick={handleClick} disabled={images.length === 0 || isLoading}>
          {isLoading ? 'Generating...' : 'Generate Video'}
        </button>

        {/* 비디오 생성 후 다운로드 버튼 표시 */}
        {videoUrl && (
          <button onClick={handleDownload}>
            Open Video
          </button>
        )}

      </div>
      <input type="text" placeholder="Enter topic text" value={topicText} onChange={(e) => setTopicText(e.target.value)} />
      {/* 제목 텍스트 폰트 사이즈 수정 */}
      <div className="font-setting">
        <label>Title Font Size:</label>
        <input
          type="number"
          value={titleFontSize}
          min="10"
          onChange={(e) => setTitleFontSize(e.target.value)}
        />
      </div>

      {/* 스크립트 텍스트 폰트 사이즈 수정 */}
      <div className="font-setting">
        <label>Script Font Size:</label>
        <input
          type="number"
          value={scriptFontSize}
          min="10"
          onChange={(e) => setScriptFontSize(e.target.value)}
        />
      </div>

      {/* 폰트 종류 선택 */}
      <div className="font-setting">
        <label>Select Font:</label>
        <select value={selectedFont} onChange={(e) => setSelectedFont(e.target.value)}>
          <option value="NanumBarunpenB">Nanum Barunpen Bold</option>
          <option value="NanumBrush">Nanum Brush</option>
          <option value="NanumGothic">Nanum Gothic</option>
          <option value="NanumGothicBold">Nanum Gothic Bold</option>
          <option value="잘난체TTF">잘난체</option>
        </select>
      </div>

      <div {...getRootProps()} className="dropzone">
        <input {...getInputProps()} />
        <p>Drag & drop images here, or click to select images</p>
      </div>

      <div className="bgm-upload">
        <label>Background Music (BGM):</label>
        <input type="file" accept="audio/*" onChange={(e) => setBgm(e.target.files[0])} />
      </div>

      <div className="images-preview">
        {images.map((image, index) => (
          <div key={index} className="image-row">
            {/* 이미지 미리보기 */}
            <img src={image.preview} alt={`Uploaded ${index}`} width="100" />

            {/* 듀레이션 입력 */}
            <div className="input-group">
              <label>Duration (초)</label>
              <input
                type="number"
                value={durations[index] || 5}
                min="1"
                onChange={handleChange(setDurations)(index)}
              />
            </div>

            {/* 애니메이션 선택 */}
            <div className="input-group">
              <label>Animation</label>
              <select value={animations[index] || 'stop'} onChange={handleChange(setAnimations)(index)}>
                {['stop', 'slide-up', 'slide-down', 'slide-left', 'slide-right'].map((anim) => (
                  <option key={anim} value={anim}>{anim}</option>
                ))}
              </select>
            </div>

            {/* 스크립트 입력 */}
            <div className="input-group">
              <textarea
                value={scripts[index] || ''}
                onChange={handleChange(setScripts)(index)}
                placeholder="Enter script text"
              />
            </div>

            {/* TTS 사용 여부 */}
            <div className="input-group">
              <label>
                <input
                  type="checkbox"
                  checked={ttsEnabled[index] || false}
                  onChange={(e) => setTtsEnabled((prev) => ({ ...prev, [index]: e.target.checked }))}
                />
                {' '}TTS 사용
              </label>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default App;
