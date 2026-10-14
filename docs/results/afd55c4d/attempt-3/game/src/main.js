import { Game } from './game.js';

const container = document.getElementById('game-container');
const game = new Game(container);
game.init();
