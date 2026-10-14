export class UI {
    constructor(container, game) {
        this.container = container;
        this.game = game;
        this.uiElements = {};
        this.createUI();
    }

    createUI() {
        const overlay = document.createElement('div');
        overlay.id = 'ui-overlay';
        overlay.style.cssText = 'position:absolute;top:0;left:0;width:100%;height:100%;pointer-events:none;';
        this.container.appendChild(overlay);

        this.createMainMenu();
        this.createCarSelection();
        this.createHUD();
        this.createCountdown();
        this.createPauseScreen();
        this.createResultsScreen();
    }

    createMainMenu() {
        const menu = document.createElement('div');
        menu.id = 'main-menu';
        menu.style.cssText = 'position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);text-align:center;pointer-events:auto;background:rgba(0,0,0,0.8);padding:40px;border-radius:10px;color:#fff;font-family:Arial,sans-serif;';
        const title = document.createElement('h1');
        title.textContent = 'TURBO RACER 3D';
        title.style.cssText = 'font-size:48px;margin-bottom:20px;text-shadow:2px 2px 4px #000;';
        menu.appendChild(title);
        const startBtn = document.createElement('button');
        startBtn.textContent = 'SELECT CAR';
        startBtn.style.cssText = 'padding:15px 30px;font-size:20px;background:#ff6600;border:none;border-radius:5px;color:#fff;cursor:pointer;margin-top:20px;';
        startBtn.onclick = () => this.showCarSelection();
        menu.appendChild(startBtn);
        const controlsInfo = document.createElement('div');
        controlsInfo.style.cssText = 'margin-top:30px;font-size:14px;text-align:left;';
        controlsInfo.innerHTML = '<strong>Controls:</strong><br>W/Up - Accelerate<br>S/Down - Brake<br>A/Left - Steer Left<br>D/Right - Steer Right<br>C - Camera<br>P/Esc - Pause<br>R - Restart';
        menu.appendChild(controlsInfo);
        this.container.appendChild(menu);
        this.uiElements.mainMenu = menu;
    }

    createCarSelection() {
        const carSelect = document.createElement('div');
        carSelect.id = 'car-selection';
        carSelect.style.cssText = 'position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);text-align:center;pointer-events:auto;background:rgba(0,0,0,0.85);padding:30px;border-radius:10px;color:#fff;font-family:Arial,sans-serif;display:none;';
        const title = document.createElement('h2');
        title.textContent = 'CHOOSE YOUR CAR';
        title.style.cssText = 'font-size:32px;margin-bottom:20px;';
        carSelect.appendChild(title);
        const carContainer = document.createElement('div');
        carContainer.style.cssText = 'display:flex;gap:20px;justify-content:center;';
        const stats = Object.values(this.game.CAR_STATS);
        stats.forEach((stat, index) => {
            const carCard = document.createElement('div');
            carCard.style.cssText = `background:${stat.color};padding:20px;border-radius:8px;cursor:pointer;width:150px;text-align:center;color:#fff;font-weight:bold;transition:transform 0.2s;`;
            carCard.innerHTML = `<div style="font-size:18px;margin-bottom:10px;">${stat.name}</div><div style="font-size:12px;">Speed: ${stat.maxSpeed}</div><div style="font-size:12px;">Accel: ${(stat.acceleration*100).toFixed(0)}%</div><div style="font-size:12px;">Handle: ${(stat.handling*100).toFixed(0)}%</div>`;
            carCard.onmouseover = () => carCard.style.transform = 'scale(1.05)';
            carCard.onmouseout = () => carCard.style.transform = 'scale(1)';
            carCard.onclick = () => this.game.selectCar(index);
            carContainer.appendChild(carCard);
        });
        carSelect.appendChild(carContainer);
        const startBtn = document.createElement('button');
        startBtn.textContent = 'START RACE';
        startBtn.style.cssText = 'padding:15px 30px;font-size:20px;background:#00cc00;border:none;border-radius:5px;color:#fff;cursor:pointer;margin-top:20px;';
        startBtn.onclick = () => this.game.startRace();
        carSelect.appendChild(startBtn);
        const backBtn = document.createElement('button');
        backBtn.textContent = 'BACK';
        backBtn.style.cssText = 'padding:10px 20px;font-size:16px;background:#666;border:none;border-radius:5px;color:#fff;cursor:pointer;margin-top:10px;';
        backBtn.onclick = () => this.showMenu();
        carSelect.appendChild(backBtn);
        this.container.appendChild(carSelect);
        this.uiElements.carSelection = carSelect;
    }

    createHUD() {
        const hud = document.createElement('div');
        hud.id = 'hud';
        hud.style.cssText = 'position:absolute;top:10px;left:10px;pointer-events:none;color:#fff;font-family:Arial,sans-serif;text-shadow:1px 1px 2px #000;display:none;';
        const speedDisplay = document.createElement('div');
        speedDisplay.id = 'speed-display';
        speedDisplay.style.cssText = 'font-size:36px;font-weight:bold;';
        hud.appendChild(speedDisplay);
        const lapDisplay = document.createElement('div');
        lapDisplay.id = 'lap-display';
        lapDisplay.style.cssText = 'font-size:20px;margin-top:5px;';
        hud.appendChild(lapDisplay);
        const positionDisplay = document.createElement('div');
        positionDisplay.id = 'position-display';
        positionDisplay.style.cssText = 'font-size:20px;margin-top:5px;';
        hud.appendChild(positionDisplay);
        const timerDisplay = document.createElement('div');
        timerDisplay.id = 'timer-display';
        timerDisplay.style.cssText = 'font-size:20px;margin-top:5px;';
        hud.appendChild(timerDisplay);
        const cameraDisplay = document.createElement('div');
        cameraDisplay.id = 'camera-display';
        cameraDisplay.style.cssText = 'position:absolute;top:10px;right:10px;font-size:16px;color:#fff;text-shadow:1px 1px 2px #000;';
        hud.appendChild(cameraDisplay);
        this.container.appendChild(hud);
        this.uiElements.hud = hud;
    }

    createCountdown() {
        const countdown = document.createElement('div');
        countdown.id = 'countdown';
        countdown.style.cssText = 'position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);font-size:120px;font-weight:bold;color:#fff;text-shadow:2px 2px 4px #000;display:none;pointer-events:none;';
        this.container.appendChild(countdown);
        this.uiElements.countdown = countdown;
    }

    createPauseScreen() {
        const pause = document.createElement('div');
        pause.id = 'pause-screen';
        pause.style.cssText = 'position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);text-align:center;pointer-events:auto;background:rgba(0,0,0,0.8);padding:40px;border-radius:10px;color:#fff;font-family:Arial,sans-serif;display:none;';
        const title = document.createElement('h2');
        title.textContent = 'PAUSED';
        title.style.cssText = 'font-size:48px;margin-bottom:20px;';
        pause.appendChild(title);
        const resumeBtn = document.createElement('button');
        resumeBtn.textContent = 'RESUME (P)';
        resumeBtn.style.cssText = 'padding:15px 30px;font-size:20px;background:#00cc00;border:none;border-radius:5px;color:#fff;cursor:pointer;margin-top:20px;';
        resumeBtn.onclick = () => this.game.togglePause();
        pause.appendChild(resumeBtn);
        const quitBtn = document.createElement('button');
        quitBtn.textContent = 'QUIT TO MENU';
        quitBtn.style.cssText = 'padding:15px 30px;font-size:20px;background:#ff6600;border:none;border-radius:5px;color:#fff;cursor:pointer;margin-top:10px;';
        quitBtn.onclick = () => this.game.restartRace();
        pause.appendChild(quitBtn);
        this.container.appendChild(pause);
        this.uiElements.pauseScreen = pause;
    }

    createResultsScreen() {
        const results = document.createElement('div');
        results.id = 'results-screen';
        results.style.cssText = 'position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);text-align:center;pointer-events:auto;background:rgba(0,0,0,0.85);padding:40px;border-radius:10px;color:#fff;font-family:Arial,sans-serif;display:none;';
        const title = document.createElement('h2');
        title.textContent = 'RACE FINISHED!';
        title.style.cssText = 'font-size:36px;margin-bottom:20px;';
        results.appendChild(title);
        const positionDiv = document.createElement('div');
        positionDiv.id = 'final-position';
        positionDiv.style.cssText = 'font-size:24px;margin-bottom:10px;';
        results.appendChild(positionDiv);
        const timeDiv = document.createElement('div');
        timeDiv.id = 'final-time';
        timeDiv.style.cssText = 'font-size:20px;margin-bottom:20px;';
        results.appendChild(timeDiv);
        const restartBtn = document.createElement('button');
        restartBtn.textContent = 'RACE AGAIN (R)';
        restartBtn.style.cssText = 'padding:15px 30px;font-size:20px;background:#00cc00;border:none;border-radius:5px;color:#fff;cursor:pointer;margin-top:20px;';
        restartBtn.onclick = () => this.game.restartRace();
        results.appendChild(restartBtn);
        const menuBtn = document.createElement('button');
        menuBtn.textContent = 'MAIN MENU';
        menuBtn.style.cssText = 'padding:15px 30px;font-size:20px;background:#ff6600;border:none;border-radius:5px;color:#fff;cursor:pointer;margin-top:10px;';
        menuBtn.onclick = () => this.game.restartRace();
        results.appendChild(menuBtn);
        this.container.appendChild(results);
        this.uiElements.resultsScreen = results;
    }

    showMenu() {
        this.uiElements.mainMenu.style.display = 'block';
        this.uiElements.carSelection.style.display = 'none';
        this.uiElements.hud.style.display = 'none';
        this.uiElements.countdown.style.display = 'none';
        this.uiElements.pauseScreen.style.display = 'none';
        this.uiElements.resultsScreen.style.display = 'none';
    }

    showCarSelection() {
        this.uiElements.mainMenu.style.display = 'none';
        this.uiElements.carSelection.style.display = 'block';
    }

    hideMenu() {
        this.uiElements.mainMenu.style.display = 'none';
        this.uiElements.carSelection.style.display = 'none';
    }

    showCountdown(value) {
        this.uiElements.countdown.textContent = value;
        this.uiElements.countdown.style.display = 'block';
    }

    updateCountdown(value) {
        this.uiElements.countdown.textContent = value;
    }

    hideCountdown() {
        this.uiElements.countdown.style.display = 'none';
    }

    showHUD() {
        this.uiElements.hud.style.display = 'block';
    }

    updateHUD(speed, lap, maxLaps, position, time) {
        this.uiElements.hud.querySelector('#speed-display').textContent = Math.floor(speed) + ' km/h';
        this.uiElements.hud.querySelector('#lap-display').textContent = `Lap ${lap}/${maxLaps}`;
        this.uiElements.hud.querySelector('#position-display').textContent = `Position: ${position}`;
        const minutes = Math.floor(time / 60);
        const seconds = ((time % 60) * 100).toFixed(0).padStart(2, '0');
        this.uiElements.hud.querySelector('#timer-display').textContent = `${minutes}:${seconds}`;
    }

    updateCameraIndicator(cameraIndex) {
        const names = ['CHASE', 'HOOD', 'OVERHEAD'];
        this.uiElements.hud.querySelector('#camera-display').textContent = `CAM: ${names[cameraIndex]}`;
    }

    showPause() {
        this.uiElements.pauseScreen.style.display = 'block';
    }

    hidePause() {
        this.uiElements.pauseScreen.style.display = 'none';
    }

    updateCarSelection(index) {
        const cards = this.uiElements.carSelection.querySelectorAll('div[onclick]');
        cards.forEach((card, i) => {
            card.style.border = i === index ? '3px solid #fff' : 'none';
        });
    }

    showResults(position, time) {
        this.uiElements.resultsScreen.querySelector('#final-position').textContent = `You finished in ${position} place!`;
        const minutes = Math.floor(time / 60);
        const seconds = ((time % 60) * 100).toFixed(0).padStart(2, '0');
        this.uiElements.resultsScreen.querySelector('#final-time').textContent = `Total Time: ${minutes}:${seconds}`;
        this.uiElements.resultsScreen.style.display = 'block';
    }
}
