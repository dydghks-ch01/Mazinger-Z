document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("analyzeForm");
  form.addEventListener("submit", (e) => {
    const title = form.title.value.trim();
    const artist = form.artist.value.trim();

    if (!title || !artist) {
      e.preventDefault();
      alert("노래 제목과 가수 이름을 모두 입력해주세요!");
    }
  });
});
