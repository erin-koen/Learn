import React from 'react';
import logo from './logo.svg';
import './App.css';

import Toggle from './ToggleRPC.js';
import Portal from './Portal.js';

function App() {
	return (
		<div className="App">
			<header className="App-header">
				<img src={logo} className="App-logo" alt="logo" />
			</header>
			<Toggle>
				{({ on, toggle }) => (
					<>
						{on && <h1>Show Me</h1>}
						<button onClick={toggle}>Show/Hide</button>
					</>
				)}
			</Toggle>
			<Portal>
				<h1>Hi, I'm in a portal.</h1>
			</Portal>
		</div>
	);
}

export default App;
