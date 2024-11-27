import express from 'express'
import fetch from 'node-fetch'              // https://www.npmjs.com/package/node-fetch
import { parse } from 'node-html-parser'    // https://www.npmjs.com/package/node-html-parser
import { encode } from 'html-entities'
const app = express()
const port = 80


async function generateGithubHistoryRSS(res, url) {
    try {
        let html = await fetch(url).then(resp => { return resp.text() })
        let github_username = url.split('/')[3]
        let github_repo = url.split('/')[4]
        let root = parse(html)
        // console.log(html)

        let rss = `<?xml version="1.0" encoding="utf-8"?>
        <rss version="2.0">
            <channel>
                <title>${github_username} - ${github_repo}: github updates</title>
                <link>${url}</link>
                <description>Github history updates</description>
        `


        for (let timeline of root.querySelectorAll('.TimelineItem')) {
            let date = timeline.querySelector('h2').text.replace('Commits on', '')
            date = (new Date(date.trim()).toUTCString())
            let title  = timeline.querySelector('a').text
            title = encode(title, {mode: 'nonAsciiPrintable', level: 'xml'})
            // let item_url = 'https://github.com' +  timeline.querySelector('a').getAttribute('href')
            rss += `
                    <item>
                        <title>${title}</title>
                        <pubDate>${date}</pubDate>
                        <link>${url}</link>
                        <description>${github_username} - ${github_repo}: Github update</description>
                    </item>
            `
            // console.log(url)
        }

        rss += `</channel>
        </rss>
        `

        // console.log(rss)
        res.set('Content-Type', 'application/xml');
        res.send(rss)
    } catch {
        res.send(`Failed to generate RSS for: ${url}`)
    }
}

// generate github rss endpoint
app.get('/generate_github_history_rss', (req, res) => {
    console.log(req.url)
    console.log(req.query.url)
    if (req.query.url && req.query.url.startsWith('https://github.com/')) {
        generateGithubHistoryRSS(res, req.query.url)
        return
    }
    res.send('Please enter a valid url.')
})

// Default message
app.get('*', (req, res) => {
    console.log(req.url)
    res.send('Please enter a valid url.')
})


app.listen(port, () => {
    console.log(`Example app listening on port ${port}`)
})