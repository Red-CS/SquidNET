const Discord = require('discord.js');

const client = new Discord.Client();

client.once('ready', () => {
    console.log("SquidNET is online!");
});

client.on('message', message => {
	console.log(message.content);
});

client.login('NjkwMDE4Njc1MDI1MjQ4MzMx.XvBj-w.Fc4CqZez-xMRPrMy1i7z7aR_PTY');