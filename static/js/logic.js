// ===============================================================================================

const COOKIE_SHOW_LOGGED_IN_MENU = "logged_in_menu"

// ===============================================================================================

// Cookie Utilities
// https://www.quirksmode.org/js/cookies.html

function createCookie(name, value, days) {
	if (days) {
		var date = new Date();
		date.setTime(date.getTime()+(days*24*60*60*1000));
		var expires = "; expires="+date.toGMTString();
	}
	else var expires = "";
	document.cookie = name+"="+value+expires+"; path=/";
}

function readCookie(name) {
	var nameEQ = name + "=";
	var ca = document.cookie.split(';');
	for(var i=0;i < ca.length;i++) {
		var c = ca[i];
		while (c.charAt(0)==' ') c = c.substring(1,c.length);
		if (c.indexOf(nameEQ) == 0) return c.substring(nameEQ.length,c.length);
	}
	return null;
}

function eraseCookie(name) {
	createCookie(name,"",-1);
}

// ===============================================================================================


firebase.auth().onAuthStateChanged((user) => {
    if (user) 
    {
        // User is signed in

        $( "#nav_link_logout" ).click(function() {
            firebase.auth().signOut().then(function() {
                //document.location.href = "/";
                eraseCookie(COOKIE_SHOW_LOGGED_IN_MENU);
            }).catch(function(error) {
                console.log(error);
            });
        });
        createCookie(COOKIE_SHOW_LOGGED_IN_MENU, 1, 0);
    }
    else
    {
        eraseCookie(COOKIE_SHOW_LOGGED_IN_MENU);
    }
});

// ===============================================================================================

if ($("body").data("page-id") == "filter") 
{
    firebase.auth().onAuthStateChanged((user) => {
        if (user) 
        {
            // User is signed in
    
            const uid = user.uid;
    
            $("#rss_feed").val(`${window.location.origin}/writeups/${uid}`)
    
            $("#filter").show();
    
            firebase.database().ref(`/data/${uid}/ctf_names`).once('value').then((snapshot) => {
                $("#ajax_loader").hide();
    
                const ctf_names = snapshot.val()?.split(ENTRY_SEPARATOR) || [];
                ctf_names.length = Math.min(ctf_names.length, MAX_CTF_ENTRIES); 
    
                const create_input_wrapper = function(){ 
                    const input_wrapper = $(`
                    <div class="input-group mb-3 ctf_name_entry">
                        <input type="text" class="form-control ctf_name_input" maxlength="${MAX_ENTRY_NAME_LEN}"
                                placeholder="CTF Name" aria-label="CTF Name" aria-describedby="basic-addon2">
                        <div class="input-group-append">
                            <button class="btn btn-outline-secondary btn-danger text-white remove_ctf_name" type="button">🗙</button>
                        </div>
                    </div>`);
                    input_wrapper.find(".remove_ctf_name").click(function(){
                        input_wrapper.remove(); 
                        show_hide_add_button();
                    });
                    return input_wrapper;
                };
    
                ctf_names.forEach(ctf_name => {
                    const input_wrapper = create_input_wrapper();
                    input_wrapper.find(".ctf_name_input").val(ctf_name);
                    $("#ctf_names").append(input_wrapper);
                });
    
                if (ctf_names.length == 0)
                {
                    $("#ctf_names").append(create_input_wrapper());
                }
    
                const ctf_names_wrapper = $("#ctf_names_wrapper");
                const add_button = $('#add_button');
                add_button.click(function(){
                    const input_wrapper = create_input_wrapper();
                    $("#ctf_names").append(input_wrapper);
                    
                    show_hide_add_button();
                    
                    ctf_names_wrapper.scrollTop(ctf_names_wrapper.prop("scrollHeight"));
                });
    
                const show_hide_add_button = function() {
                    ($(".ctf_name_input").length < MAX_CTF_ENTRIES) ? add_button.show() : add_button.hide();   
                };
    
                show_hide_add_button();
                
                $("#copy_rss_feed_link").click(function(){
                    const copyText = document.getElementById("rss_feed");
                    copyText.select();
                    copyText.setSelectionRange(0, $(copyText).val().length); // For mobile devices
                    document.execCommand("copy");
                }).popover({ trigger: "manual", placement: "top" }).click(function() { 
                    var pop = $(this); 
                    pop.popover("show") 
                    pop.on('shown.bs.popover',function() { 
                    setTimeout(function() {
                        pop.popover("hide")
                    }, 1000); 
                    });
                });
    
                
                $('#save_button').click(function(){
                    const ctf_names_arr = [];
                    $(".ctf_name_entry").each(function(index, elem) {
                        const element = $(elem);
                        const name = element.find(".ctf_name_input").val();
                        if ( (name.trim() != "") && (!ctf_names_arr.includes(name)) )
                        {
                            ctf_names_arr.push(name);
                        }
                        else
                        {
                            element.remove();
                        }
                    });
                    const new_ctf_names = ctf_names_arr.join(ENTRY_SEPARATOR);
                    firebase.database().ref('data/' + uid).set({
                        ctf_names: new_ctf_names
                    }, (error) => {
                        const modal = $("#saveModal")
                        if (error) 
                        {
                            modal.find("#saveModalLongTitle").text("Error");
                            modal.find(".modal-body").text("An error ocurred while trying to save your changes.");
                        } 
                        else 
                        {
                            modal.find("#saveModalLongTitle").text("Changes Saved");
                            modal.find(".modal-body").text("Your changes were saved successfully. Your feed will reflect them automatically.");
                        }
                        modal.modal('show');
                    });
                })
                .show();
    
            });
        } 
        else 
        {
            document.location.href = "/login";
        }
    });
}

// ===============================================================================================

if ($("body").data("page-id") == "login") 
{
    firebase.auth().onAuthStateChanged((user) => {
        if (user) 
        {
            document.location.href = "/filter";
        } 
        else 
        {
            var uiConfig = 
            {
                callbacks: {
                    signInSuccessWithAuthResult: function(authResult, redirectUrl) 
                    {
                        // User successfully signed in.
                        // Return type determines whether we continue the redirect automatically (true)
                        // or whether we leave that to developer to handle (false).
                        createCookie(COOKIE_SHOW_LOGGED_IN_MENU, 1, 0);
                        return true;
                    },
                    uiShown: function() 
                    {
                        // The widget is rendered.
                        $(".firebaseui-title").text("Sign in / Sign up with email")
                    }
                },
                'credentialHelper': firebaseui.auth.CredentialHelper.NONE,
                
                //signInFlow: 'popup',
                signInSuccessUrl: '/filter',
                signInOptions: [
                    {
                        provider: firebase.auth.EmailAuthProvider.PROVIDER_ID,
                        requireDisplayName: false
                    }
                ],
    
                // Terms of service url
                tosUrl: '/tos'
            };
    
            const ui = firebaseui.auth.AuthUI.getInstance() || new firebaseui.auth.AuthUI(firebase.auth());
            ui.start('#firebaseui-auth-container', uiConfig);
            
        }
    });
}

// ===============================================================================================