// debounce for X time, then call buildTable
let TIMEOUT = 750;
let timer;
function debounceBuildTable() {
    clearTimeout(timer);
    timer = setTimeout(buildTable, TIMEOUT);
}


function resetFilters() {
    document.getElementById("reset-btn").classList.add("pure-button-disabled")
    document.getElementById("reset-btn").disabled = true
    
    document.getElementById("search").value = ""
    document.getElementById("ecosystem").selectedIndex = 0
    document.getElementById("lang").selectedIndex = 0
    document.getElementById("cvss-min").value = ""
    document.getElementById("cvss-max").value = ""
    debounceBuildTable();

    document.getElementById("reset-btn").classList.remove("pure-button-disabled")
    document.getElementById("reset-btn").disabled = false
}




let currentPage = 0;
const itemsPerPage = 100;
let filtered_data = [];

function buildTable() {
    let table = document.querySelector("table");
    let search_term = document.getElementById("search").value || "";
    let ecosystem = document.getElementById("ecosystem").selectedOptions[0].value || "all";
    let lang = document.getElementById("lang").selectedOptions[0].value || "all";
    let cvss_min = document.getElementById("cvss-min").value || "";
    let cvss_max = document.getElementById("cvss-max").value || "";

    // Filter the data based on the search and filters
    filtered_data = data.filter(function(row) {
        return (
            (ecosystem == "all" || row.ecosystem == ecosystem) && 
            (lang == "all" || row.langs.match(new RegExp("\\b" + lang + "\\b", "i"))) &&
            (row.summary + row.details).match(new RegExp(search_term, "i")) &&
            (cvss_min == "" || parseFloat(row.severity) >= parseFloat(cvss_min)) &&
            (cvss_max == "" || parseFloat(row.severity) <= parseFloat(cvss_max))
        );
    });

    updateDropdowns(filtered_data);

    // Reset the table and page number
    table.innerHTML = "";
    currentPage = 0;
    
    // Load the initial data
    loadMoreData();
    

}

function loadMoreData() {
    console.log("Loading more data...")
    let search_term = document.getElementById("search").value || "";
    let table = document.querySelector("table");

    // Determine the starting and ending index for the current page
    const startIndex = currentPage * itemsPerPage;
    const endIndex = Math.min(startIndex + itemsPerPage, filtered_data.length);

    // Create document fragment to append the rows
    let fragment = document.createDocumentFragment();

    // Append the rows for the current page
    for (let i = startIndex; i < endIndex; i++) {
        let row = filtered_data[i];
        let row_ele = document.createElement("tr");
        row_ele.innerHTML = `
            <td>${row.ecosystem}</td>
            <td><a href="https://osv.dev/vulnerability/${row.id}" target="_blank">${row.id}</a></td>
            <td class="padded summary" style="text-align: left; max-width: 60em">${row.summary ? `<b>${row.summary}</b><br>` : ""}${row.details}</td>
            <td>${row.published.replace("T", "<br>")}</td>
            <td class="padded">${row.severity}</td>
            <td class="padded">${row.langs}</td>
            <td class='references' style="text-align: left; max-width: 30em">
                <ul>
                    ${row.references}
                </ul>
            </td>
        `;
        fragment.appendChild(row_ele);
    }

    table.appendChild(fragment);


    // Highlight the search term
    for (let ele of table.querySelectorAll(".summary")) {
        let instance = new Mark(ele);
        instance.markRegExp(new RegExp(search_term, "i"));
    }

    // mark references    
    for (let ele of table.querySelectorAll(".references")) {
        let inst = new Mark(ele)
        inst.markRegExp(new RegExp("/[^/]*?#L\\d+"))
    }
    // Increment the page for the next load
    currentPage++;
}

// Add an event listener to handle scrolling and load more data when needed
window.addEventListener('scroll', () => {
    if (window.scrollY + window.innerHeight >= document.documentElement.scrollHeight) {
        loadMoreData();
    }
});





function updateDropdowns(data) {
    let ecosystems = {}
    let langs = {}

    // keep track of counts
    for (let row of data) {
        ecosystems[row.ecosystem] = ecosystems[row.ecosystem] + 1 || 1;
        for (let lang of row.langs.split("\n")) {
            if (lang == "") continue
            langs[lang] = langs[lang] + 1 || 1;
        }
    }

    
    ecosystems = Object.fromEntries(Object.entries(ecosystems).sort(([, valueA], [, valueB]) => valueB - valueA));
    langs = Object.fromEntries(Object.entries(langs).sort(([, valueA], [, valueB]) => valueB - valueA));

    let ecosystem_dropdown = document.getElementById("ecosystem");
    let lang_dropdown = document.getElementById("lang");

    for (let option of ecosystem_dropdown.children) {
        let orig_count = option.getAttribute("data-orig-count")
        if (orig_count) {
            let filtered_count = ecosystems[option.value] || 0
            option.textContent = `${option.value} (${orig_count}) (${filtered_count})`
        }
    }

    for (let option of lang_dropdown.children) {
        let orig_count = option.getAttribute("data-orig-count")
        if (orig_count) {
            let filtered_count = langs[option.value] || 0
            option.textContent = `${option.value} (${orig_count}) (${filtered_count})`
        }
    }


}

function buildDropdowns(data) {
    let ecosystems = {}
    let langs = {}

    // keep track of counts
    for (let row of data) {
        ecosystems[row.ecosystem] = ecosystems[row.ecosystem] + 1 || 1;
        for (let lang of row.langs.split("\n")) {
            if (lang == "") continue
            langs[lang] = langs[lang] + 1 || 1;
        }
    }

    
    ecosystems = Object.fromEntries(Object.entries(ecosystems).sort(([, valueA], [, valueB]) => valueB - valueA));
    langs = Object.fromEntries(Object.entries(langs).sort(([, valueA], [, valueB]) => valueB - valueA));

    let ecosystem_dropdown = document.getElementById("ecosystem");
    let lang_dropdown = document.getElementById("lang");

    // build ecosystem dropdown
    let ecosystem_options = Object.keys(ecosystems).map(function(ecosystem) {
        return `<option data-orig-count="${ecosystems[ecosystem]}" value="${ecosystem}">${ecosystem} (${ecosystems[ecosystem]})</option>`
    });

    ecosystem_dropdown.innerHTML = `<option value="all">All ecosystems</option>` + ecosystem_options.join("");

    // build lang dropdown
    let lang_options = Object.keys(langs).map(function(lang) {
        return `<option data-orig-count="${langs[lang]}" value="${lang}">${lang} (${langs[lang]})</option>`
    });

    lang_dropdown.innerHTML = `<option value="all">All languages</option>` + lang_options.join("");
}







buildDropdowns(data);
buildTable();