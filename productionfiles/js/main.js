window.onload = function() {
    var startBtn = document.getElementById('start-btn');
    var textArea = document.getElementById('text-area');
    var recognition = new webkitSpeechRecognition();
    recognition.continuous = true;
    recognition.interimResults = true;

    startBtn.addEventListener('click', function() {
        recognition.start();
    });

    recognition.onresult = function(event) {
        var result = event.results[event.results.length - 1];
        textArea.innerHTML = result[0].transcript;
    };

    recognition.onerror = function(event) {
        console.log(event.error);
    };
};
