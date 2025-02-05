import express from 'express'
import fetch from 'node-fetch'              // https://www.npmjs.com/package/node-fetch
import { parse } from 'node-html-parser'    // https://www.npmjs.com/package/node-html-parser
import { encode } from 'html-entities'
import puppeteer from 'puppeteer';
const app = express()
const port = 80


async function getCode4RenaReports(res) {
    try {
        const url = "https://code4rena.com/reports"
        const browser = await puppeteer.launch({
            executablePath: '/usr/bin/chromium',
            args: ['--no-sandbox', '--disable-setuid-sandbox'],
        });
        const page = await browser.newPage();
        await page.goto(url, {waitUntil: 'networkidle2'});
        const html = await page.content();
        await browser.close();
        res.send(html)
    } catch (e){
        res.send('Failed to fetch code4rena reports: ' + e)
    }
}

async function generateGithubHistoryRSS(res, url) {
    try {
        let html = await fetch(url).then(resp => { return resp.text() })
        let github_username = url.split('/')[3]
        let github_repo = url.split('/')[4]
        let root = parse(html)
        // console.log(html)

        let rss = `<?xml version="1.0" encoding="utf-8"?>
        <rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">
            <channel>
                <title>${github_username} - ${github_repo}: github updates</title>
                <link>${url}</link>
                <description>Github history updates</description>
        `


        for (let timeline of root.querySelectorAll("[class*='TimelineBody-']")) {
            let date = timeline.querySelector('h3').text.replace('Commits on', '')
            date = (new Date(date.trim()).toUTCString())
            let title  = timeline.querySelector('a').text
            title = encode(title, {mode: 'nonAsciiPrintable', level: 'xml'})
            // let item_url = 'https://github.com' +  timeline.querySelector('a').getAttribute('href')
            rss += `
                    <item>
                        <guid>${url}-${date}-${title}</guid>
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
    if (req.query.url && req.query.url.startsWith('https://github.com/')) {
        generateGithubHistoryRSS(res, req.query.url)
        return
    }
    res.send('Please enter a valid url.')
})

app.get('/fetch_code4rena_reports', (req, res) => {
    getCode4RenaReports(res)
})


// Default message
app.get('*', (req, res) => {
    console.log(req.url)
    res.send('Not a valid endpoint.')
})


app.listen(port, () => {
    console.log(`Example app listening on port ${port}`)
})