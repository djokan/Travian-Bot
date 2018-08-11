# Travian-Bot
Bot is initially forked from https://github.com/ruodeng/Travian-Bot.

Usage:

Bot has auto queue feature for building.

It reads config.json file (not example_config.json) to get configuration.

config.json

username[mandatory]:  uername of player.

password[mandatory]: password of player.

headers[mandatory]: web browser header. It is highly recommended to go to link: https://pgl.yoyo.org/http/browser-headers.php and use User-Agent field as headers.

proxies[optional]: proxy server that bot will use.

villages[mandatory]: a set of allplayer villages.

example:
  "villages": {
    "[vid]": {
      "id": [vid],
      "buildType": "[buildtype]"
    },
    "[vid]": {
      "id": [vid],
      "buildType": "[buildtype]"
    }
  }

    [vid]: village id (can be obtained from link when village name on right side clicked. It is number and can be found after at newdid= in link.
  
    [buildtype]: can be "resource"- build minimal level resource field which resource amount is minimal.
  
  
  
