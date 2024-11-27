# github-history-rss

The purpose of this repo is to stand up a server that can generate a valid .rss of the github history page. When trying to track histroy using [inoreader.com](inoreader.com), each update to the repo will re-create (duplicate) notifications for all old commits. This project acts as middleware to generate an RSS feed, creating one rss item for each day a github repo was committed to.

## Usage

**Start**:
```bash
# local testing
npm run start

# run on server
nohup npm run start &
```

**Test using url**:
```
/generate_github_history_rss?url=https://github.com/httpvoid/writeups/commits/main
```