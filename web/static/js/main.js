document.addEventListener('DOMContentLoaded', (event) => {
    const socket = io.connect(location.protocol + '//' + document.domain + ':' + location.port);

    const statusBar = document.getElementById('status-bar');
    const questionText = document.getElementById('question-text');
    const hintContainer = document.getElementById('hint-container');
    const teamOneName = document.getElementById('team-one-name');
    const teamOneScore = document.getElementById('team-one-score');
    const teamTwoName = document.getElementById('team-two-name');
    const teamTwoScore = document.getElementById('team-two-score');
    const timerDisplay = document.getElementById('timer');

    function updateStatusBar(rounds) {
        statusBar.innerHTML = ''; // Clear existing circles
        rounds.forEach((status, index) => {
            const circle = document.createElement('div');
            circle.classList.add('status-circle', status);
            circle.textContent = index + 1;
            statusBar.appendChild(circle);
        });
    }

    function updateHints(hints) {
        hintContainer.innerHTML = '';
        if (hints.length > 0) {
            hints.forEach(hintText => {
                const p = document.createElement('p');
                p.textContent = hintText;
                hintContainer.appendChild(p);
            });
        }
    }

    socket.on('connect', () => {
        console.log('Websocket connected!');
    });

    socket.on('game_update', (data) => {
        console.log('Received game update:', data);

        if (data.question !== undefined) {
            questionText.textContent = data.question;
        }
        
        if (data.hints !== undefined) {
            updateHints(data.hints);
        }

        if (data.team_names !== undefined) {
            teamOneName.textContent = data.team_names[0];
            teamTwoName.textContent = data.team_names[1];
        }
        if (data.scores !== undefined) {
            teamOneScore.textContent = data.scores[0];
            teamTwoScore.textContent = data.scores[1];
        }
        if (data.rounds !== undefined) {
            updateStatusBar(data.rounds);
        }
        if (data.time_left !== undefined) {
            timerDisplay.textContent = data.time_left;
            if (data.time_left <= 5) {
                timerDisplay.classList.add('flashing');
            } else {
                timerDisplay.classList.remove('flashing');
            }
        } else {
            timerDisplay.textContent = '';
            timerDisplay.classList.remove('flashing');
        }
    });
});
