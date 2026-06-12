let searchBox = document.getElementById('searchInput');
let filterBox = document.getElementById('FilterSection')
let url = ''
let FilterForm = document.getElementById('FilterForm')


FilterForm.addEventListener('submit', async () => {
    let formObj = new FormData(FilterForm);

//This is where we collect the fields the user is given to fill out for the filter form
const queryParams = {
    q: formObj.get('LocationInput') || '',
    min_price: formObj.get('FilterMinPrice') || '', // Match the camelCase keys your Flask backend expects
    max_price: formObj.get('FilterMaxPrice') || '',
    min_acres: formObj.get('FilterMinAcres') || '',
    max_acres: formObj.get('FilterMaxAcres') || '',
    zoning: formObj.get('zoningFilter') || '',
    qct: formObj.get('QCT/DDA_Stat') || '',
    terrain: formObj.get('Terrain_Filter') || ''
};

//Use URLSearchParams to cleanly build the query string side-by-side
const searchParams = new URLSearchParams();

for (const [key, value] of Object.entries(queryParams)) {
    // Only append the filter if the user actually typed or selected something!
    if (value !== '') {
        searchParams.append(key, value);
    }
}

// This will add all our search arguments or parameters to the get request
let url = `/api/propertyFilter?${searchParams.toString()}`;

console.log("Generated Fetch URL:", url);
// Output will look like: /api/property?q=Hartford&minPrice=100000&zoning=Residential
    try{
        const response = await fetch(url, {
            method: 'GET',
        });

        const data = await response.json();
        console.log(data);
    } catch(error){
        console.error("Error fetching properties:", error);
    }
})

async function loadProperties() {
    //This will get us the address that the user has inputted into the search bar
    let searchValue = encodeURIComponent(searchBox.value.trim()); //Gets

    //We will only add the q argument if the user has typed in a search value
    if(searchValue !== ''){
        url = `/api/propertySearch?q=${searchValue}`;
    } else {
        url = `/api/propertySearch`;
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