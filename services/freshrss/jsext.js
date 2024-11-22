
let title_color_map = {
    "0xdf": "yellow",
}

setInterval(() => {
    let titles = document.querySelectorAll("span[class='websiteName']")
    for (let t of titles) {
        for (let [search_text, color] of Object.entries(title_color_map)) {
            if (t.innerText.includes(search_text)) {
                t.style.backgroundColor = color
            }
        }
    }
}, 1000)