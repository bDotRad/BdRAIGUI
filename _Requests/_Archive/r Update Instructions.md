

Update the instructions in _BdRGUI/_Instructions/Requests.md
then update the code if required.

request files will start with simply "r " and be of type .md
folders will start with "rf " and will have a request.md file in them
the folders purpose is to contain other files for reference.
so unless otherwise stated, no other docs are to be referenced...especially in the archived folder.

A request file is ready to be scanned when the word READY is written on line one and nothing else.
So you only need to scan the first line of type .md and starting with an r.


Second part.

Update the instructions in _BdRGUI/_Instructions/BdRGUI.md
then update the code if required.

Rename everything named BdRGUI to BdRAIGUI. Or any text on the pages.

Id like a simple text input that allows me to create a .md file in the Reqest folder for that project.
Then if possible, make a folder with a .md file and attachments.

The intent is to eventually be able to to it through tailscale. so if it needs to go to a prefolder first thats ok.
bascially a way to put .md files somewhere and the system grabs them then processes them.

I also want this to be pushed to GitHub. Its been setup to push to bdotrad. theres a config file somewhere.



● User answered Claude's questions:
  ⎿  · What's the GitHub owner/org for the BdRAIGUI repo? → mailbradm

● Write(.ssh/config)
  ⎿  Wrote 5 lines to .ssh/config
      1 Host github.com-bdraigui
      2     HostName github.com
      3     User git
      4     IdentityFile ~/.ssh/bdraigui_deploy_key
      5     IdentitiesOnly yes

  Ran 1 shell command

● The deploy key works — GitHub confirms it's authenticated for bDotRad/BdRAIGUI. SSH config is set up at ~/.ssh/config.

  Want me to clone the repo now using this key? If so, where should it go (e.g. ~/BdRAIGUI)?

✻ Sautéed for 21s

❯ yep

  Ran 1 shell command

● Cloned successfully into ~/BdRAIGUI — it's just an empty repo on GitHub currently. The deploy key is fully wired up and working end-to-end.

✻ Sautéed for 8s
                        