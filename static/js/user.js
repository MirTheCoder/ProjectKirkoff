let loginForm = document.getElementById('loginForm')
let accountForm = document.getElementById('accountForm')
let addANote = document.getElementById('notes')
let noteForm = document.getElementById('noteOverlay')
let closeNotes = document.getElementById('closeNotes')
let loginRender = document.getElementById('login')
let loginOverlay = document.getElementById('loginOverlay')
let accountOverlay = document.getElementById('accountOverlay')
let closeLogin = document.getElementById('closeLogin')
let closeAccount = document.getElementById('closeAccount')
let logout = document.getElementById('logout')
let saveProp = document.getElementById('Save')
let seeSavedProps = document.getElementById('seeSavedProps')
let savedProp = document.getElementById('savedPropSection')
let savedPropPrice = document.getElementById('savedPropPrice')
let SavedPropSize = document.getElementById('SavedPropSize')
let savedPropAddress = document.getElementById('savedPropAddress')

//We will use this function to have the username and password combo checked and if it is verified, it will be saved to our users list
accountForm.addEventListener('submit', async (e) => {
     e.preventDefault();
     let formObj = new FormData(accountForm);
     let formData = Object.fromEntries(formObj.entries())
     url = `${BACKEND_URL}/api/addProperties`
    url = BACKEND_URL + '/users/createAccount'
    const response = await fetch(url, {
            method: 'POST',
            headers: {
            'Content-Type': 'application/json'
            },
            body: JSON.stringify(formData)
        });

    //Our check to see whether or not the account creation was successful
    let data = await response.json();

    if (data.ok) {
        alert('Your account has been successfully created');
    } else {
    alert('Your account is already taken');
    }

})

//We will use this function to have the user logged in and verify that their credentials are accurate
loginForm.addEventListener('submit', async (e) => {
    e.preventDefault();
     let formObj = new FormData(loginForm);
     let formData = Object.fromEntries(formObj.entries())
     url = `${BACKEND_URL}/api/addProperties`
    url = BACKEND_URL + '/users/login'
    const response = await fetch(url, {
            method: 'POST',
            headers: {
            'Content-Type': 'application/json'
            },
            body: JSON.stringify(formData)
    });

    //Our check to see whether or not the Login was successful
    let data = await response.json()
    if (data.ok) {
        alert('You have been successfully logged in, welcome ', data.username);
        //Reloads the main page essentially
        window.location.href = BACKEND_URL
    } else {
        alert('The credentials that you have entered are invalid');
    }

});

createAccount.addEventListener('click', () => {
    if(!accountOverlay.classList.contains('active')){
        accountOverlay.classList.add('active')
    }
})

//Allows users to close out the account creation pop up box
closeAccount.addEventListener('click', closeAccountOverlay)

async function closeAccountOverlay(){
    if(accountOverlay.classList.contains('active')){
        accountOverlay.classList.remove('active')
    }
}

//This will handle rendering the popup login page
loginRender.addEventListener('click', () => {
    if(!loginOverlay.classList.contains('active')){
        loginOverlay.classList.add('active');
    }
    closeLogin.addEventListener('click', closeLoginPage);
})

//This will close the login page
async function closeLoginPage(){
    if(loginOverlay.classList.contains('active')){
        loginOverlay.classList.remove('active');
    }
    closeLogin.removeEventListener('click', closeLoginPage) //Remove listener from the close button
}

async function seeNoteCard(){
    if(!noteForm.classList.contains('active')){
        noteForm.classList.add('active')
        closeNotes.addEventListener('click', closeNotePage)
    }

    //Using this to get the address element and input the actual address of the property that the users wants to leave a note on
    let propertyName = noteForm.querySelector('#noteAddress')
    propertyName.innerHTML = `${propLocation.textContent.trim()}`


    addANote.removeEventListener('click', seeNoteCard)
}

async function closeNotePage(){
     if(noteForm.classList.contains('active')){
        noteForm.classList.remove('active')
        closeNotes.removeEventListener('click', closeNotePage)
    }
}


//This will handle the logout logic to ensure that the screen and details get updated whenever the user log out to show
//that the user is indeed logged out
logout.addEventListener('click', async () => {
    url = BACKEND_URL + '/logout'
    const response = await fetch(url, {
            method: 'GET',
    });

    data = await response.json();

    if(data.ok){
        alert('You have successfully been logged out')
    } else {
        alert('You are not logged in')
    }

    window.location.reload()
})

seeSavedProps.addEventListener('click', async () => {
    url = BACKEND_URL + '/api/saved-properties'
    const response = await fetch(url, {
            method: 'GET',
    });

    data = await response.json();
    if(data.ok){
        await displaySavedProps(data.props)
    } else {
        alert('You need to be logged in, in order to view your saved Properties')
    }
})

//This will handle the saved property logic for our system
saveProp.addEventListener('click', async (e) => {
    let panel = e.target.closest('#detailsPanel');
    let address = panel.querySelector('#DetailAddress').textContent.trim(); //This will get us the property of the location
    //that the user is trying to save

    //We will pass it to te backend to see if te property has already been saved, and if the user is logged in
    //user must be l
    url = BACKEND_URL + '/users/saveProp'
    const response = await fetch(url, {
            method: 'POST',
            headers: {
            'Content-Type': 'application/json'
            },
            body: JSON.stringify({"address": address})
    });

    let data = await response.json()

    //We will use this to write back a response on the status of the action of saving the property for the user
    if(data.ok){
        if(data.saved){
            alert("property has successfully been saved and can be viewed in your saved property list")
        } else {
            alert("property is already in your saved list")
        }
    } else {
        alert('Must be logged in to save property')
    }
})

//This function will display all the users saved properties
async function displaySavedProps(props){
    if(props.length > 0){
        savedPropSection.innerHTML = ``
        props.forEach(prop => {
            let savedDiv = document.createElement('div')
            savedDiv.innerHTML = `<div class="p-4 pb-0">
                <img src="/static/images/DefaultBuilding.jpeg"
                     alt="Property Image"
                     class="w-full h-48 object-cover rounded-lg shadow-sm" />
                </div>

              <div class="p-6 flex-1 overflow-y-auto space-y-6">

                <div>
                  <span class="text-xs font-semibold uppercase tracking-wider text-slate-400" id="savedPropLocation">Location</span>
                  <h4 id="savedPropAddress" class="text-xl font-bold text-slate-800 mt-1">${prop.address}</h4>
                </div>
              </div>

              <hr class="border-slate-100" />

                <div class="grid grid-cols-2 gap-4 bg-slate-50 p-4 rounded-xl">
                  <div>
                    <span class="block text-xs font-medium text-slate-500 uppercase" >Price</span>
                    <p id="savedPropPrice" class="text-lg font-bold text-emerald-600 mt-0.5">${prop.price}</p>
                  </div>
                  <div>
                    <span class="block text-xs font-medium text-slate-500 uppercase">Size (Acres)</span>
                    <p id="SavedPropSize" class="text-lg font-bold text-slate-800 mt-0.5">${prop.size_acres}</p>
                  </div>
                </div>

              <hr class="border-slate-100" />

              <div class="p-4 border-t border-slate-100 bg-slate-50 flex items-center justify-end gap-5">
              <button id="closeSavePage" type="button" class="px-4 py-2 bg-slate-200 hover:bg-slate-300 text-slate-700 font-medium text-sm rounded-lg transition-colors cursor-pointer">
                Close
              </button>

               <button id="removeProp" type="button" class="px-4 py-2 bg-slate-200 hover:bg-slate-300 text-slate-700 font-medium text-sm rounded-lg transition-colors cursor-pointer">
                Remove
              </button>
            </div>`

        savedPropSection.appendChild(savedDiv)

        if(savedPropSection.classList.contains('hidden')){
            savedPropSection.classList.remove('hidden')
        }
        })
    } else {
        savedPropSection.innerHTML = "You have no properties saved at this time"

        if(savedPropSection.classList.contains('hidden')){
            savedPropSection.classList.remove('hidden')
        }
    }

}