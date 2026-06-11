let searchBox = document.getElementById('searchInput');
let url = ''

async function loadProperties() {
    //This will get us the address that the user has inputted into the search bar
    let searchValue = encodeURIComponent(searchBox.value.trim()); //Gets

    //We will only add the q argument if the user has typed in a search value
    if(searchValue !== ''){
        url = `/api/property?q=${searchValue}`;
    } else {
        url = `http://localhost:5000/api/property`;
    }

    try {
        const response = await fetch(url, {
            method: 'GET',
        });

        const data = await response.json();
        console.log(data); // Ready to use your data here!
    } catch (error) {
        console.error("Error fetching properties:", error);
    }
}