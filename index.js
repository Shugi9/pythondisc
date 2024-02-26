const fs = require('fs'), { Client, GatewayIntentBits } = require('discord.js'), axios = require('axios'), Database = require('better-sqlite3'), config = require('./config.json'), YouTube = require('youtube-sr').default, TwitchJs = require('twitch-js').default, sharp = require('sharp'), db = new Database('db.db'), client = new Client({ intents: [GatewayIntentBits.Guilds, GatewayIntentBits.GuildMessages, GatewayIntentBits.MessageContent, GatewayIntentBits.GuildMembers,], }), p = [], n = [];

client.once('ready', () => console.log(`Logged in as ${client.user.tag}!`));

setInterval(() => console.log(db.prepare('SELECT * FROM t WHERE id = ?').get('id')), 30000);

setInterval(async () => {
    let c = client.channels.cache.get(config.twitchid);
    if (!c) return console.log("Invalid channel configured.");

    let rs = axios.create(), body = { 'client_id': config.clientid, 'client_secret': config.clientsecret, "grant_type": 'client_credentials' }, r = await rs.post('https://id.twitch.tv/oauth2/token', body), keys = r.data, token = keys['access_token'];

    for (let t of config.twitchChannels) {
        let url = "https://api.twitch.tv/helix/streams?user_login=" + t, headers = { 'Client-ID': config.clientid, 'Authorization': 'Bearer ' + token }, req = await axios.get(url, { headers: headers }), res = req.data;

        if (res['data'].length > 0) {
            let data = res['data'][0], streamid = data["id"];
            if (!n.includes(streamid)) {
                n.push(streamid);
                let game_name = data["game_name"], message = `**<@&1039329011173699734> ${t} is Live** \n🚨https://www.twitch.tv/${t} 🚨`;
                if (game_name) message += `\nPlaying: ${game_name}`;
                message += " 👍";
                await c.send(message);
            }
        }
    }
}, 60000);

setInterval(async () => {
    try {
        let c = client.channels.cache.get(config.youtubeid);
        if (!c) return console.log("Invalid channel configured.");
        const v = await YouTube.search(config.ytchannel, { limit: 3 });
        v.forEach(video => { if (!p.includes(video.id)) p.push(video.id); });
    } catch (exc) { console.log(`Error: ${exc}`); }
}, 60000);

// Send the sticky message every 12 seconds
setInterval(async () => {
    const channel = client.channels.cache.get(config.stickyChannelId);
    if (channel) {
        channel.send(config.stickyMessage);
    }
}, 12000);
client.on('guildCreate', async guild => {});

client.login(config.token);
