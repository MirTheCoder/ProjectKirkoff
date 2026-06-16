let searchBox = document.getElementById('searchInput');
let filterBox = document.getElementById('FilterSection')
let url = ''
let FilterForm = document.getElementById('FilterForm')
let tableRowData = document.getElementById('propertyRows') //Where our properties will be displayed
let resetFilterForm = document.getElementById('FilterReset')
let closeOverlay1 = document.getElementById('closeOverlayProperty')
let overlayProperty = document.getElementById('overlayProperty')
let detailPanel = document.getElementById('detailsPanel')
let closeDetails = document.getElementById('closeDetails')
let propLocation = document.getElementById('DetailAddress')
let propPrice = document.getElementById('DetailPrice')
let propSize = document.getElementById('DetailSize')
let propType = document.getElementById('DetailType')
let propZone = document.getElementById('Zone')
let propTerrain = document.getElementById('Terrain')
let propUtilities = document.getElementById('DetailUtilities')
let propFema = document.getElementById('DetailFema')
let propFeasibility = document.getElementById('DetailFeasibility')
let QCT_DDA = document.getElementById('QCT_DDA')
let LastUpdated = document.getElementById('DetailUpdated')
let DDA = document.getElementById('DDA')
let addPropertyForm = document.getElementById('addProperty')

const BACKEND_URL = 'http://127.0.0.1:5001'; //This assures that our code hits the correct port number

//Using this to create our free map which will be centered at east berlin CT, these are the coordinates for berlin Connecticut
    const map = L.map('map').setView([41.6150, -72.7112], 15);
    L.control.zoom({position: 'bottomright'}).addTo(map)

    //This will be used to create a layer group that will store our markers so that it will be easier to
    //remove the markers
    const layerGroup = L.layerGroup().addTo(map)

    //This will hold all the qct areas
    const QCTLayers = L.layerGroup().addTo(map)

//We will load all the properties that we have once the page loads and renders itself
document.addEventListener('DOMContentLoaded', async () => {
    const response = await fetch(`${BACKEND_URL}/api/propertySearch`, {
            method: 'GET',
        });

        const data = await response.json();
        await showProperties(data)

    if(overlayProperty && overlayProperty.classList.contains('active')){ //This is to check if the overlay is already active and visible on the page
            overlay.classList.remove('active'); //This will make the overlay invisible on the page
    }

    L.tileLayer('https://api.maptiler.com/maps/streets-v4/{z}/{x}/{y}.png?key=PYjzqRSFEwN74Wyenzcs', {
        attribution: `<a href="https://www.maptiler.com/copyright/" target="_blank">&copy; MapTiler</a> <a href="https://www.openstreetmap.org/copyright" target="_blank">&copy; OpenStreetMap contributors</a>` //Make sure to add this in order to give credit to the website "cloud.maptiler.com"
    }).addTo(map)

    await getQCTCoordinates()
    await getDDACoordinates()


})



//We will use this reset button to reset the data the user put within the form to default values along with rendering
//all properties
async function resetFilter(){
    FilterForm.reset();

    url = `${BACKEND_URL}/api/propertySearch`;
    const response = await fetch(url, {
            method: 'GET',
        });

        const data = await response.json();
        await showProperties(data)

};

//Thi function will help to save the property that a user saves
addPropertyForm.addEventListener('submit', async (e) => {
     e.preventDefault();
     let formObj = new FormData(addPropertyForm);
     url = `${BACKEND_URL}/api/addProperties`

     const response = await fetch(url, {
            method: 'POST',
            headers: {
            'Content-Type': 'application/json'
            },
            body: formObj
        });
})

FilterForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    let formObj = new FormData(FilterForm);
    //This will clear all the markers from
    layerGroup.clearLayers();

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
let url = `${BACKEND_URL}/api/propertyFilter?${searchParams.toString()}`;

// Output will look like: /api/property?q=Hartford&minPrice=100000&zoning=Residential
    try{
        const response = await fetch(url, {
            method: 'GET',
        });

        const data = await response.json();
        await showProperties(data)
    } catch(error){
        console.error("Error fetching properties:", error);
    }
})

async function loadProperties() {
    //This will clear all the markers from
    layerGroup.clearLayers();

    //This will get us the address that the user has inputted into the search bar
    let searchValue = encodeURIComponent(searchBox.value.trim()); //Gets

    //We will only add the q argument if the user has typed in a search value
    if(searchValue !== ''){
        url = `${BACKEND_URL}/api/propertySearch?q=${searchValue}`;
    } else {
        url = `${BACKEND_URL}/api/propertySearch`;
    }

    try {
        const response = await fetch(url, {
            method: 'GET',
        });

        const data = await response.json();
        await showProperties(data)
    } catch (error) {
        console.error("Error fetching properties:", error);
    }
}

//This function will populate our rows with the properties that either match the users search or filter
async function showProperties(data){
    tableRowData.innerHTML = '' //Reset the table to nothing so that we can populate it according to the users search or query

    //Checking to make sure that our data is in array format, else we will turn it into array format
    //if(!data.isArray()){
        //data = data.toArray()
    //}

    //Only want to populate the property table if we actually got results back for the users search or filter
    if(data.length > 0){
        data.forEach(prop => {
            let row = document.createElement('tr')
            let data1 = document.createElement('td')
            let data2 = document.createElement('td')
            let data3 = document.createElement('td')
            let data4 = document.createElement('td')
            let data5 = document.createElement('td')
            let data6 = document.createElement('td')
            let data7 = document.createElement('td')
            let data8 = document.createElement('td')
            let data9 = document.createElement('td')

            data1.innerHTML = `${prop.address}`
            data1.id = "add" //This will help su easily find the address of the property we want to view in detail
            data1.style.margin = 'auto';
            row.appendChild(data1)
            data2.innerHTML = `${prop.city}`
            data2.style.margin = 'auto';
            row.appendChild(data2)
            data3.innerHTML = `$${prop.price}`
            data3.style.margin = 'auto';
            row.appendChild(data3)
            data4.innerHTML = `${prop.size_acres}`
            data4.style.margin = 'auto';
            row.appendChild(data4)
            data5.innerHTML = `${prop.qct_status}`
            data5.style.margin = 'auto';
            row.appendChild(data5)
            data6.innerHTML = `${prop.utilities}`
            data6.style.margin = 'auto';
            row.appendChild(data6)
            data7.innerHTML = `${prop.terrain}`
            data7.style.margin = 'auto';
            row.appendChild(data7)
            data8.innerHTML = `${prop.feasibility_score}`
            data8.style.margin = 'auto';
            row.appendChild(data8)
            data9.innerHTML = `<button id="DetailsButton"
            class="inline-flex items-center gap-1 px-2.5 py-1 bg-blue-600 hover:bg-blue-500 active:scale-[0.97] text-white text-xs font-bold rounded-md border border-slate-950 shadow-[1px_1px_0px_0px_rgba(2,6,23,1)] hover:shadow-none hover:translate-x-[1px] hover:translate-y-[1px] focus:outline-none focus:ring-1 focus:ring-blue-400 focus:ring-offset-1 transition-all duration-150 cursor-pointer select-none">
            See Details
            </button>`
            data9.style.margin = 'auto';
            row.appendChild(data9)


            tableRowData.appendChild(row)

            //We will use this to mark the property on the map by adding it to the layerGroup
            let marker = L.marker([prop.lat, prop.lng]).addTo(layerGroup);

        });
        detailButtonListener();
    }

}

//This will render the overlay page where users can add their property to the lisitng
async function openAddPropertyModal(){
    if(overlayProperty && !overlayProperty.classList.contains('active')){ //This is to check if the overlay is already active and visible on the page
            overlayProperty.classList.add('active'); //This will make the overlay invisible on the page
    }

    //This will be used to close the overlay box that allows users to add property
    if(closeOverlay1){
        closeOverlay1.addEventListener('click', () =>
            overlayProperty.classList.remove('active')
        )
    }
}

//Our fetch call to backend to get the qct coordinates
async function getQCTCoordinates(){
    url = `${BACKEND_URL}/api/getQCT`;
    const response = await fetch(url, {
            method: 'GET',
        });

        const data = await response.json();
        console.log(data) //Allows us to see how the data looks exactly
        await displayQCTCoordinates(data)
}



//Our fetch call to backend to get the dda coordinates
async function getDDACoordinates(){
    url = `${BACKEND_URL}/api/getDDA`;
    const response = await fetch(url, {
            method: 'GET',
        });

        const data = await response.json();
        console.log(data)
        await displayDDACoordinates(data)
}



//This will be the function we use to display the qct areas using their coordinates
async function displayQCTCoordinates(features){

    for(const feature of features){
        let pointArray = []
    //Grabs all the coordinate points that make up that one qct area
    try{
 //Will be used to ensure that we don't run into an error incase the fields we request aren't present
        points = feature['geometry']['rings'][0]

        for([x,y] of points){
            pointArray.push([y,x]) //The Leaflet system reads the lat and long in the reverse way that Hud API sends it, so we have to swap each coordinate
        }

        //We will add the points directly to the
        let polygon1 = L.polygon(pointArray, {color: 'purple',
            fillColor: '#9370DB',
            fillOpacity: 0.5
        }).addTo(QCTLayers);
    } catch(err){
        console.log('The results stopped here')
        break
    }

    }
}

//This will be the function we use to display the qct areas using their coordinates
async function displayDDACoordinates(features){
let count = 1
    for(const feature of features) {
        let pointArray = []
    //Grabs all the coordinate points that make up that one qct area
        try{
            points = feature['geometry']['rings'][0]
            for([x,y] of points){
                pointArray.push([y,x]) //The Leaflet system reads the lat and long in the reverse way that Hud API sends it, so we have to swap each coordinate
            }

            //We will add the points directly to the
            let polygon2 = L.polygon(pointArray, {color: 'orange',
                fillColor: '#FFA500',
                fillOpacity: 0.5
            }).addTo(QCTLayers);
        } catch(err) {
            console.log('Results stop here')
            break;
        }
    }
}

//This will toggle our side view screen that will display the details of the property the user selects or clicks on
async function detailButtonListener(){
    if(document.querySelectorAll('#DetailsButton')){
        let buttons = document.querySelectorAll('#DetailsButton')
        buttons.forEach(button => {
            button.addEventListener('click', async (e) => {
                let tableData = e.target.closest('tr')
                let propdata = tableData.querySelector("#add").textContent.trim() //This will get the specific address for the property that we want to view and look at
                await getPropViaAddress(propdata)
                if(detailPanel.classList.contains('hidden')){
                    detailPanel.classList.remove('hidden');
                    closeButtonListener()
                }
            })
        })

    }

}


//Using this to hide the detail panel of the close button is clicked
async function closeButtonListener(){
        closeDetails.addEventListener('click', closeDetailPanel)
}

async function closeDetailPanel(){
    if(!detailPanel.classList.contains('hidden')){
        detailPanel.classList.add('hidden')
    }
    closeDetails.removeEventListener('click', closeDetailPanel)
}



async function getPropViaAddress(propdata){
    url = `${BACKEND_URL}/api/addressForProp?address=${propdata}`; //We will pass the users
    const response = await fetch(url, {
            method: 'GET',
        });

        const propData = await response.json();
        console.log(propData)
        await displayDetails(propData[0])
}


//


//This will fill our display page with the details of the property in question
async function displayDetails(propData){
    propLocation.innerHTML = `${propData.address}`
    propPrice.innerHTML = `$${propData.price}`
    propSize.innerHTML = `${propData.size_acres}`
    propType.innerHTML = `${propData.property_type}`
    propZone.innerHTML = `${propData.zoning}`
    propTerrain.innerHTML = `${propData.terrain_level}`
    propUtilities.innerHTML = `${propData.utilities}`
    propFema.innerHTML = `${propData.fema_zone}`
    propFeasibility.innerHTML = `${propData.feasibility_score}`
    QCT_DDA.innerHTML = `${propData.qct_status}`
    DDA.innerHTML = `${propData.dda_status}`
    LastUpdated.innerHTML = `${propData.last_updated}`
}

//Sets up variables to receive the required variables needed for turning addresses into lat and long coordinates on the map


