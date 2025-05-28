document.addEventListener("DOMContentLoaded", function () {
    // ✅ 1. 마이크 기능 (search1.html 전용)
    const micBtn = document.getElementById('mic-btn');
    if (micBtn) {
        const micIcon = micBtn.querySelector('i');
        const promptInput = document.getElementById('prompt-input');
        let recognition = null;
        let isRecording = false;

        micBtn.addEventListener('click', () => {
            const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
            if (!SpeechRecognition) {
                alert("이 브라우저는 음성 인식을 지원하지 않습니다.");
                return;
            }

            if (!isRecording) {
                recognition = new SpeechRecognition();
                recognition.lang = 'ko-KR';
                recognition.interimResults = false;
                recognition.maxAlternatives = 1;

                recognition.start();
                isRecording = true;
                micIcon.classList.remove('fa-microphone');
                micIcon.classList.add('fa-stop');

                recognition.onresult = (event) => {
                    promptInput.value = event.results[0][0].transcript;
                };

                recognition.onerror = (event) => {
                    alert("음성 인식 오류: " + event.error);
                };

                recognition.onend = () => {
                    isRecording = false;
                    micIcon.classList.remove('fa-stop');
                    micIcon.classList.add('fa-microphone');
                };
            } else {
                recognition.stop();
                isRecording = false;
                micIcon.classList.remove('fa-stop');
                micIcon.classList.add('fa-microphone');
            }
        });
    }

    // ✅ 2. 추천 이유 팝업 기능 (results.html 전용)
    const popup = document.getElementById("reason-popup");
    const popupText = document.getElementById("reason-text");
    const popupTitle = document.getElementById("reason-title");

    if (popup && popupText && popupTitle) {
        document.querySelectorAll('.hover-box').forEach(box => {
            const reason = box.dataset.reason;
            const parentItem = box.closest('.item');
            const label = parentItem?.querySelector('p > strong')?.innerText || '';

            if (reason && label) {
                box.addEventListener('mouseenter', () => {
                    popupTitle.innerText = `"${label}"의 추천 이유`;
                    popupText.innerText = reason;
                    popup.classList.remove("reason-popup-hidden");
                });
                box.addEventListener('mouseleave', () => {
                    popup.classList.add("reason-popup-hidden");
                });
            }
        });
    }
});

// ✅ 로딩 오버레이 트리거
document.addEventListener('DOMContentLoaded', () => {
  const recommendForm = document.getElementById('recommendForm');
  if (recommendForm) {
    recommendForm.addEventListener('submit', () => {
      document.getElementById('loadingOverlay').style.display = 'flex';
    });
  }
});

