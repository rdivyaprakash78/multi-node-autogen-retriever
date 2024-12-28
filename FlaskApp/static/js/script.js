const record = document.getElementById("recordButton");
const textarea = document.getElementById("inputArea");
const submit = document.getElementById("submitButton");
const answerArea = document.getElementById("finalAnswer");
const consoleArea = document.getElementById("console");

let seconds = 0;
let funcId = null;

function formatTime(seconds) {
  const minute = Math.floor(seconds / 60);
  const second = seconds % 60;
  formatted_minute = minute.toString().padStart(2, "0");
  formatted_seconds = second.toString().padStart(2, "0");
  record.innerHTML = `${formatted_minute}:${formatted_seconds}`;
}
function updateTime() {
  seconds++;
  formatTime(seconds);
}

function stopTimer() {
  clearInterval(funcId);
  seconds = 0;
  funcId = null;
}

function startTimer() {
  if (funcId == null) {
    funcId = setInterval(updateTime, 1000);
  }
}

submit.addEventListener("click", (e) => {
  e.preventDefault();
  let question = textarea.value;

  answerArea.style.setProperty("color", "rgb(176, 171, 171)", "important");
  answerArea.innerHTML = "Processing your question";
  consoleArea.innerHTML = "";

  const formData = new FormData();
  formData.append("question", question);

  fetch("/answer", {
    method: "POST",
    body: formData,
  })
    .then((response) => {
      return response.json();
    })
    .then((data) => {
      //answerArea.style.color = "rgb(0, 0, 0)";
      window.location.href = data.redirect;
    });
});

if (navigator.mediaDevices.getUserMedia()) {
  function setupSuccess(stream) {
    console.log("setup success");
    mediarecorder = new MediaRecorder(stream);

    record.addEventListener("click", (e) => {
      e.preventDefault();
      if (mediarecorder.state == "recording") {
        mediarecorder.stop();
        stopTimer();
        record.style.backgroundColor = "rgb(3,182,87)";
        record.innerHTML = "Record";
      } else {
        mediarecorder.start();
        startTimer();
        record.innerHTML = "00:00";
        record.style.backgroundColor = "rgb(243, 154, 12)";
      }

      let chunks = [];
      mediarecorder.ondataavailable = (e) => {
        chunks.push(e.data);
      };

      mediarecorder.onstop = () => {
        textarea.style.color = "rgb(176, 171, 171)";
        textarea.value = "Transcribing your voice";

        const blob = new Blob(chunks, { type: "audio/webm" });
        chunks = []; // resetting chunks on stop

        const formData = new FormData();
        formData.append("audio", blob);

        fetch("/upload", {
          method: "POST",
          body: formData,
        })
          .then((response) => response.json())
          .then((data) => {
            textarea.style.color = "rgb(0, 0, 0)";
            textarea.value = data.transcript;
          });
      };
    });
  }

  function setupFailure(err) {
    console.log("setup failure");
  }

  navigator.mediaDevices
    .getUserMedia({ audio: true })
    .then(setupSuccess)
    .catch(setupFailure);
} else alert("Your browzer dont support audio recording");
