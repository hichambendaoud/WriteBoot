window.onload = function() {
    const startBtn = document.querySelector('#start-btn');
    const stopBtn = document.querySelector('#stop-btn');
    const textDiv = document.querySelector('#text');

    let recognition = null;

    if (!('webkitSpeechRecognition' in window)) {
        alert("Your browser doesn't support Web Speech API!");
    } else {
        recognition = new webkitSpeechRecognition();
        recognition.continuous = true;
        recognition.interimResults = true;
        recognition.lang = 'ar-EG';

        recognition.onstart = function() {
            console.log('Speech recognition started');
            startBtn.disabled = true;
            stopBtn.disabled = false;
        };

        recognition.onresult = function(event) {
            let interimText = '';
            for (let i = event.resultIndex; i < event.results.length; ++i) {
                if (event.results[i].isFinal) {
                    const text = event.results[i][0].transcript;
                    interimText += text;
                }
            }
            textDiv.value = interimText;
        };

        recognition.onerror = function(event) {
            console.error('Speech recognition error', event);
        };

        recognition.onend = function() {
            console.log('Speech recognition ended');
            startBtn.disabled = false;
            stopBtn.disabled = true;
        };
    }

    startBtn.onclick = function() {
        recognition.start();
    };

    stopBtn.onclick = function() {
        recognition.stop();
    };

    // Send audio data to server for recognition
    recognition.onresult = function(event) {
        let interimText = '';
        let finalText = '';
        for (let i = event.resultIndex; i < event.results.length; ++i) {
            if (event.results[i].isFinal) {
                const text = event.results[i][0].transcript;
                finalText += text;
            } else {
                const text = event.results[i][0].transcript;
                interimText += text;
            }
        }

        textDiv.value = interimText;

        if (finalText) {
            
                textDiv.value = finalText;
            
        }
    };
};

function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}
