// debounce for X time, then call buildTable
let TIMEOUT = 1000;
let timer;
function debounce() {
    clearTimeout(timer);
    timer = setTimeout(buildTable, TIMEOUT);
}



function buildTable() {
    let table = document.querySelector("table");
    // let data = window.data
    let search_term = document.getElementById("search").value || ""
    let ecosystem = document.getElementById("ecosystem").selectedOptions[0].value || "all"
    let lang = document.getElementById("lang").selectedOptions[0].value || "all"
    let cvss_min = document.getElementById("cvss-min").value || ""
    let cvss_max = document.getElementById("cvss-max").value || ""
    
    let filtered_data = data.filter(function(row) {
        return (
            ecosystem == "all" || row.ecosystem == ecosystem) && 
            (lang == "all" || row.langs.match(new RegExp("\\b" + lang + "\\b", "i"))) &&
            (row.summary + row.details).match(new RegExp(search_term, "i")) &&
            (cvss_min == "" || parseFloat(row.severity) >= parseFloat(cvss_min)) &&
            (cvss_max == "" || parseFloat(row.severity) <= parseFloat(cvss_max))

    });



    updateDropdowns(filtered_data);


    let fragment = document.createDocumentFragment();
    for (let row of filtered_data) {
        let row_ele = document.createElement("tr");
        row_ele.innerHTML = `
            <td>${row.ecosystem}</td>
            <td><a href="https://osv.dev/vulnerability/${row.id}" target="_blank">${row.id}</a></td>
            <td class="padded" style="text-align: left; max-width: 60em">${row.summary ? `<b>${row.summary}</b><br>` : ""}${row.details}</td>
            <td>${row.published.replace("T", "<br>")}</td>
            <td class="padded">${row.severity}</td>
            <td class="padded">${row.langs}</td>
            <td style="text-align: left; max-width: 30em">
                <ul>
                    ${row.references}
                </ul>
            </td>
            `

            
        fragment.appendChild(row_ele);  
    }
    table.innerHTML = "";
    table.appendChild(fragment);

    // Highlight the search_term
    const instance = new Mark(table);
    instance.markRegExp(new RegExp(search_term, "i"));
}    

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