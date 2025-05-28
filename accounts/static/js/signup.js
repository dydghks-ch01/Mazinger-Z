// 페이지 로드 시 실행되는 메인 로직
document.addEventListener("DOMContentLoaded", function () {
  // 1️⃣ 주요 요소 선택
  const usernameInput = document.getElementById("id_username");
  const checkMessage = document.getElementById("username-check");
  const passwordInput = document.getElementById("id_password1");
  const passwordCheck = document.getElementById("password-check");
  const phoneInput = document.getElementById("id_phone_number");

  // 2️⃣ 전화번호 입력 시 자동 하이픈 및 유효성 검사
  function formatPhoneNumber(value) {
    const cleaned = value.replace(/\D/g, "").slice(0, 11); // 숫자만 추출, 최대 11자리
    if (cleaned.length < 4) return cleaned;
    if (cleaned.length < 8) return `${cleaned.slice(0, 3)}-${cleaned.slice(3)}`;
    return `${cleaned.slice(0, 3)}-${cleaned.slice(3, 7)}-${cleaned.slice(7, 11)}`;
  }

  function validatePhoneNumber(number) {
    return /^010-\d{4}-\d{4}$/.test(number);
  }

  if (phoneInput) {
  const phoneCheck = document.getElementById("phone-check");

  phoneInput.addEventListener("input", () => {
    phoneInput.value = formatPhoneNumber(phoneInput.value);

    if (validatePhoneNumber(phoneInput.value)) {
      phoneInput.classList.remove("error");
      phoneInput.classList.add("success");
      phoneCheck.textContent = "올바른 전화번호 형식입니다.";
      phoneCheck.className = "check-msg success";
    } else {
      phoneInput.classList.remove("success");
      phoneInput.classList.add("error");
      phoneCheck.textContent = "전화번호는 010-1234-5678 형식으로 입력해주세요.";
      phoneCheck.className = "check-msg error";
    }
  });
}


  // 3️⃣ 아이디 중복 확인 + 최소 2글자 검사
  if (usernameInput) {
    usernameInput.addEventListener("input", function () {
      const username = usernameInput.value.trim();

      if (!username) {
        checkMessage.textContent = "";
        checkMessage.className = "check-msg"; // 상태 초기화
        return;
      }

      if (username.length < 2) {
        checkMessage.textContent = "아이디는 최소 2글자 이상이어야 합니다.";
        checkMessage.className = "check-msg error";
        return;
      }

      // ✅ AJAX로 중복 확인
      fetch(`/accounts/check_username/?username=${encodeURIComponent(username)}`)
        .then(res => res.json())
        .then(data => {
          if (data.available) {
            checkMessage.textContent = "사용 가능한 아이디입니다.";
            checkMessage.className = "check-msg success";
          } else {
            checkMessage.textContent = "이미 사용 중인 아이디입니다.";
            checkMessage.className = "check-msg error";
          }
        })
        .catch(() => {
          checkMessage.textContent = "서버 오류";
          checkMessage.className = "check-msg warning";
        });
    });
  }

  // 4️⃣ 비밀번호 조건 검사 (8자 이상 & 숫자만 금지)
  if (passwordInput) {
    passwordInput.addEventListener("input", function () {
      const pw = passwordInput.value;
      if (pw.length < 8) {
        passwordCheck.textContent = "비밀번호는 8자 이상이어야 합니다.";
        passwordCheck.className = "check-msg error";
      } else if (/^\d+$/.test(pw)) {
        passwordCheck.textContent = "숫자만으로는 사용할 수 없습니다.";
        passwordCheck.className = "check-msg error";
      } else {
        passwordCheck.textContent = "사용 가능한 비밀번호입니다.";
        passwordCheck.className = "check-msg success";
      }
    });
  }
});

// 5️⃣ 이메일 인증번호 발송 및 확인
document.addEventListener("DOMContentLoaded", function () {
  const sendCodeBtn = document.getElementById('send-code-btn');
  const verifyCodeBtn = document.getElementById('verify-code-btn');
  const emailInput = document.getElementById('id_email');
  const emailSendMsg = document.getElementById('email-send-msg');
  const emailVerifyMsg = document.getElementById('email-verify-msg');
  let verified = false;

  // 인증번호 발송 버튼 클릭
  sendCodeBtn.addEventListener('click', () => {
    const email = emailInput.value.trim();

    // ✅ 이메일 형식 검사
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email)) {
      emailSendMsg.textContent = '올바른 이메일 형식을 입력하세요.';
      emailSendMsg.className = 'check-msg error';
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
        emailSendMsg.className = 'check-msg success';
      } else {
        emailSendMsg.textContent = data.error || '발송 실패';
        emailSendMsg.className = 'check-msg error';
      }
    })
    .catch(() => {
      emailSendMsg.textContent = '서버 오류';
      emailSendMsg.className = 'check-msg warning';
    });
  });

  // 인증번호 확인 버튼 클릭
  verifyCodeBtn.addEventListener('click', () => {
    const code = document.getElementById('email-code-input').value.trim();

    if (!code) {
      emailVerifyMsg.textContent = '인증번호를 입력하세요.';
      emailVerifyMsg.className = 'check-msg error';
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
        emailVerifyMsg.className = 'check-msg success';
        verified = true;
      } else {
        emailVerifyMsg.textContent = '인증번호가 올바르지 않습니다.';
        emailVerifyMsg.className = 'check-msg error';
      }
    })
    .catch(() => {
      emailVerifyMsg.textContent = '서버 오류';
      emailVerifyMsg.className = 'check-msg warning';
    });
  });
});

// 6️⃣ 프로필 아이콘 선택 로직
document.addEventListener("DOMContentLoaded", function () {
  const iconOptions = document.querySelectorAll('.icon-option');
  const hiddenInput = document.getElementById('selected-profile-picture');

  iconOptions.forEach(option => {
    option.addEventListener('click', () => {
      // 모든 선택 해제 후 선택한 아이콘만 강조
      iconOptions.forEach(o => o.classList.remove('selected'));
      option.classList.add('selected');

      // 선택된 값(hidden input에 저장)
      const selectedValue = option.getAttribute('data-value');
      hiddenInput.value = selectedValue;
    });
  });
});
