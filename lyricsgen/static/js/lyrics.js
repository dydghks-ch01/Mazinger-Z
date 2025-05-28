// 🎤 음성 인식
const micBtn = document.getElementById('mic-btn');
const stopBtn = document.getElementById('stop-recognition');
const promptInput = document.getElementById('prompt-input');

let recognition = null;
let isManuallyStopped = false;

micBtn?.addEventListener('click', () => {
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SpeechRecognition) {
    alert("이 브라우저는 음성 인식을 지원하지 않습니다.");
    return;
  }

  recognition = new SpeechRecognition();
  recognition.lang = 'ko-KR';
  recognition.interimResults = false;
  recognition.maxAlternatives = 1;

  recognition.start();
  micBtn.style.display = "none";
  stopBtn.style.display = "inline";

  recognition.onresult = (event) => {
    const transcript = event.results[0][0].transcript;
    promptInput.value = transcript;
    stopMicRecognitionUI();
  };

  recognition.onerror = (event) => {
    if (!isManuallyStopped) {
      alert("음성 인식 오류: " + event.error);
    }
    stopMicRecognitionUI();
  };

  recognition.onend = () => {
    stopMicRecognitionUI();
    isManuallyStopped = false;
  };
});

stopBtn?.addEventListener('click', () => {
  if (recognition) {
    isManuallyStopped = true;
    recognition.stop();
  }
  stopMicRecognitionUI();
});

function stopMicRecognitionUI() {
  micBtn.style.display = "inline";
  stopBtn.style.display = "none";
}

// 🔎 Ajax로 가사 상세 정보 가져오기
function openLyricsModalById(id) {
  fetch(`/lyrics/api/${id}/`)
    .then(res => res.json())
    .then(data => {
      openLyricsModal(data.prompt, data.lyrics, data.image_url, data.id);
    })
    .catch(err => {
      alert("가사를 불러오는 데 실패했습니다: " + err);
    });
}

// 🪟 모달 표시
function showLyricsModal(title, lyrics, imageUrl, id) {
  console.log("모달 열기:", { title, lyrics, imageUrl, id });

  const modalImage = document.getElementById("modalImage");
  const modalTitle = document.getElementById("modalTitle");
  const modalLyrics = document.getElementById("modalLyrics");
  const modal = document.getElementById("lyricsModal");
  const backdrop = document.getElementById("modalBackdropLyrics");

  if (!modalImage || !modalTitle || !modalLyrics || !modal || !backdrop) {
    alert("모달 요소를 찾을 수 없습니다.");
    return;
  }

  modalTitle.textContent = title;
  modalLyrics.innerHTML = lyrics.replace(/\n/g, "<br>");
  modalImage.src = imageUrl;

  modal.style.display = "flex";
  backdrop.style.display = "block";
}

// ⭐ 즐겨찾기
function toggleFavorite(lyricsId) {
  fetch(`/lyrics/favorite/${lyricsId}/`, {
    method: 'POST',
    headers: {
      'X-CSRFToken': getCookie('csrftoken'),
    }
  })
    .then(res => res.json())
    .then(data => {
      if (data.status === 'ok') {
        alert(data.is_favorite ? "즐겨찾기에 추가됨" : "즐겨찾기 해제됨");
        location.reload();  // 또는 버튼 텍스트만 바꾸기
      }
    })
    .catch(err => alert("즐겨찾기 실패: " + err));
}

// ✅ CSRF 토큰 읽기 함수
function getCookie(name) {
  let cookieValue = null;
  if (document.cookie && document.cookie !== '') {
    const cookies = document.cookie.split(';');
    for (let i = 0; i < cookies.length; i++) {
      const cookie = cookies[i].trim();
      if (cookie.startsWith(name + '=')) {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
        break;
      }
    }
  }
  return cookieValue;
}

// ✅ 로딩 오버레이 트리거
document.querySelector('form.header-form')?.addEventListener('submit', () => {
  document.getElementById('loadingOverlay').style.display = 'flex';
});
document.querySelectorAll('form.ai-image-form').forEach(form => {
  form.addEventListener('submit', () => {
    document.getElementById('loadingOverlay').style.display = 'flex';
  });
});

