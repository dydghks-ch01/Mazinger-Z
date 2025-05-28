document.addEventListener("DOMContentLoaded", function () {
  // 이메일 관련 요소
  const sendCodeBtn = document.getElementById('send-code-btn');
  const emailInput = document.getElementById('email');
  const emailCodeInput = document.getElementById('email-code-input');
  const emailVerifyMsg = document.getElementById('email-verify-msg');

  // 전화번호 관련 요소
  const phoneInput = document.getElementById("phone");
  const phoneErrorMsg = document.createElement("span");
  phoneErrorMsg.className = "check-msg";
  phoneInput.insertAdjacentElement("afterend", phoneErrorMsg);

  let verified = false;

  // ✅ 이메일 인증번호 전송
  sendCodeBtn.addEventListener('click', () => {
    const email = emailInput.value.trim();

    // 이메일 형식 검사
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email)) {
      emailVerifyMsg.textContent = '올바른 이메일 형식을 입력하세요.';
      emailVerifyMsg.className = 'check-msg error';
      emailInput.style.border = "2px solid red";
      return;
    }

    // 서버로 인증번호 전송
    fetch('/accounts/send_verification_code/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: `email=${encodeURIComponent(email)}`
    })
    .then(res => res.json())
    .then(data => {
      if (data.success) {
        emailVerifyMsg.textContent = '인증번호가 발송되었습니다.';
        emailVerifyMsg.className = 'check-msg success';
        emailInput.style.border = "2px solid lightgreen";
      } else {
        emailVerifyMsg.textContent = data.error || '발송 실패';
        emailVerifyMsg.className = 'check-msg error';
        emailInput.style.border = "2px solid red";
      }
    })
    .catch(() => {
      emailVerifyMsg.textContent = '서버 오류';
      emailVerifyMsg.className = 'check-msg warning';
      emailInput.style.border = "2px solid orange";
    });
  });

  // ✅ 이메일 입력 시 실시간 유효성 검사
  emailInput.addEventListener("input", () => {
    const email = emailInput.value.trim();
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

    if (emailRegex.test(email)) {
      emailInput.style.border = "2px solid lightgreen";
      emailVerifyMsg.textContent = "올바른 이메일 형식입니다.";
      emailVerifyMsg.className = "check-msg success";
    } else {
      emailInput.style.border = "2px solid red";
      emailVerifyMsg.textContent = "올바른 이메일 형식을 입력하세요.";
      emailVerifyMsg.className = "check-msg error";
    }
  });

  // 인증번호 입력 시 상태 초기화
  emailCodeInput.addEventListener('input', () => {
    verified = false;
  });

  // ✅ 전화번호 입력 시 자동 하이픈 및 유효성 검사
  function formatPhoneNumber(value) {
    const cleaned = value.replace(/\D/g, "").slice(0, 11);
    if (cleaned.length < 4) return cleaned;
    if (cleaned.length < 8) return `${cleaned.slice(0, 3)}-${cleaned.slice(3)}`;
    return `${cleaned.slice(0, 3)}-${cleaned.slice(3, 7)}-${cleaned.slice(7, 11)}`;
  }

  function validatePhoneNumber(number) {
    return /^010-\d{4}-\d{4}$/.test(number);
  }

  phoneInput.addEventListener("input", () => {
    phoneInput.value = formatPhoneNumber(phoneInput.value);

    if (validatePhoneNumber(phoneInput.value)) {
      phoneInput.style.border = "2px solid lightgreen";
      phoneErrorMsg.textContent = "올바른 형식입니다.";
      phoneErrorMsg.className = "check-msg success";
    } else {
      phoneInput.style.border = "2px solid red";
      phoneErrorMsg.textContent = "010-1234-5678 형식으로 입력하세요.";
      phoneErrorMsg.className = "check-msg error";
    }
  });
});
