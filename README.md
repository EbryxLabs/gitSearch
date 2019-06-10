# Introduction
A utility to filter github repos having user-provided keywords and then do static code analysis on targeted repos for secrets using [foresthog.](https://pypi.org/project/forestHog/)

### Sample Usage
Program uses github api to search on repos and you'll have to have a GitHub API token ready.
```
python script.py --gtoken <API_TOKEN> --search <KEYWORD>
````
`--search` requires a keyword you want to search in repos on github.
  
You can take a look at available options using `-h` option too.
```
usage: script.py [-h] [--gtoken GTOKEN] [--search SEARCH] [--rules RULES]
                 [--add-rules ADD_RULES] [--entropy] [--entropy-wc ENTROPY_WC]
                 [--entropy-b64-thresh ENTROPY_B64_THRESH]
                 [--entropy-hex-thresh ENTROPY_HEX_THRESH]

optional arguments:
  -h, --help            show this help message and exit
  --gtoken GTOKEN       Github access token for REST API.
  --search SEARCH       Keyword to search in Github's all repo code.
  --rules RULES         Ignore default regexes and source from json list file
  --add-rules ADD_RULES
                        Adds more regex rules along with default ones from a
                        json list file
  --entropy             Enable entropy checks
  --entropy-wc ENTROPY_WC
                        Segments n-length words to check entropy against
                        [default: 20]
  --entropy-b64-thresh ENTROPY_B64_THRESH
                        User defined entropy threshold for base64 strings
                        [default: 4.5]
  --entropy-hex-thresh ENTROPY_HEX_THRESH
                        User defined entropy threshold for hex strings
                        [default: 3.0]
```