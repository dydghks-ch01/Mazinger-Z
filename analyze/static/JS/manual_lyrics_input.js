document.addEventListener("DOMContentLoaded", () => {
  const form = document.querySelector("form");
  const textarea = document.querySelector("textarea");

  form?.addEventListener("submit", (e) => {
    if (!textarea.value.trim()) {
      e.preventDefault();
      alert("가사를 입력해주세요!");
    }
  });

  const cancelBtn = document.querySelector(".button.cancel");
  cancelBtn?.addEventListener("click", (e) => {
    if (!confirm("정말 다시 입력하시겠어요?")) {
      e.preventDefault();
    }
  });
});
