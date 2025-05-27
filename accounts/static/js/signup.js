document.addEventListener("DOMContentLoaded", function () {
  const usernameInput = document.getElementById("id_username");
  const checkMessage = document.getElementById("username-check");
  const passwordInput = document.getElementById("id_password1");
  const passwordCheck = document.getElementById("password-check");
  const phoneInput = document.getElementById("id_phone_number");

  // 전화번호 자동 하이픈 및 유효성
  function formatPhoneNumber(value) {
    const cleaned = value.replace(/\D/g, "").slice(0, 11);
    if (cleaned.length < 4) return cleaned;
    if (cleaned.length < 8) return `${cleaned.slice(0, 3)}-${cleaned.slice(3)}`;
    return `${cleaned.slice(0, 3)}-${cleaned.slice(3, 7)}-${cleaned.slice(7, 11)}`;
  }

  function validatePhoneNumber(number) {
    return /^010-\d{4}-\d{4}$/.test(number);
  }

  if (phoneInput) {
    phoneInput.addEventListener("input", () => {
      phoneInput.value = formatPhoneNumber(phoneInput.value);

      if (validatePhoneNumber(phoneInput.value)) {
        phoneInput.style.border = "2px solid lightgreen";
      } else {
        phoneInput.style.border = "2px solid red";
      }
    });
  }

  // 아이디 중복 체크
  if (usernameInput) {
    usernameInput.addEventListener("input", function () {
      const username = usernameInput.value.trim();
      if (!username) {
        checkMessage.textContent = "";
        return;
      }

      fetch(`/accounts/check_username/?username=${encodeURIComponent(username)}`)
        .then(res => res.json())
        .then(data => {
          if (data.available) {
            checkMessage.textContent = "사용 가능한 아이디입니다.";
            checkMessage.style.color = "lightgreen";
          } else {
            checkMessage.textContent = "이미 사용 중인 아이디입니다.";
            checkMessage.style.color = "red";
          }
        })
        .catch(() => {
          checkMessage.textContent = "서버 오류";
          checkMessage.style.color = "orange";
        });
    });
  }

  // 비밀번호 조건 검사 (JS 실시간 피드백)
  if (passwordInput) {
    passwordInput.addEventListener("input", function () {
      const pw = passwordInput.value;
      if (pw.length < 8) {
        passwordCheck.textContent = "비밀번호는 8자 이상이어야 합니다.";
        passwordCheck.style.color = "red";
      } else if (/^\d+$/.test(pw)) {
        passwordCheck.textContent = "숫자만으로는 사용할 수 없습니다.";
        passwordCheck.style.color = "red";
      } else {
        passwordCheck.textContent = "사용 가능한 비밀번호입니다.";
        passwordCheck.style.color = "lightgreen";
      }
    });
  }
});

// 인증번호 발송 및 확인
document.addEventListener("DOMContentLoaded", function () {
  const sendCodeBtn = document.getElementById('send-code-btn');
  const verifyCodeBtn = document.getElementById('verify-code-btn');
  const emailInput = document.getElementById('id_email');
  const emailSendMsg = document.getElementById('email-send-msg');
  const emailVerifyMsg = document.getElementById('email-verify-msg');
  let verified = false;

  sendCodeBtn.addEventListener('click', () => {
    const email = emailInput.value.trim();
    if (!email) {
      emailSendMsg.textContent = '이메일을 입력하세요.';
      emailSendMsg.style.color = 'red';
      return;
    }

    fetch('/accounts/send_verification_code/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: `email=${encodeURIComponent(email)}`
    })
    .then(res => res.json())
    .then(data => {
      if (data.success) {
        emailSendMsg.textContent = '인증번호가 발송되었습니다.';
        emailSendMsg.style.color = 'green';
      } else {
        emailSendMsg.textContent = data.error || '발송 실패';
        emailSendMsg.style.color = 'red';
      }
    });
  });

  verifyCodeBtn.addEventListener('click', () => {
    const code = document.getElementById('email-code-input').value.trim();
    if (!code) {
      emailVerifyMsg.textContent = '인증번호를 입력하세요.';
      emailVerifyMsg.style.color = 'red';
      return;
    }

    fetch('/accounts/verify_email_code/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: `code=${encodeURIComponent(code)}`
    })
    .then(res => res.json())
    .then(data => {
      if (data.verified) {
        emailVerifyMsg.textContent = '인증되었습니다.';
        emailVerifyMsg.style.color = 'green';
        verified = true;
      } else {
        emailVerifyMsg.textContent = '인증번호가 올바르지 않습니다.';
        emailVerifyMsg.style.color = 'red';
      }
    });
  });
});

