
var WriteupFeedFilter = WriteupFeedFilter || {};

// ===============================================================================================

WriteupFeedFilter.CookieUtils = {};
(function(context) 
{ 
    // Based on https://www.quirksmode.org/js/cookies.html
    context.createCookie = function(name, value, days) 
    {
        let expires;
        if (days) 
        {
            const date = new Date();
            date.setTime(date.getTime() + (days * 24 * 60 * 60 * 1000));
            expires = "; expires=" + date.toGMTString();
        }
        else 
        {
            expires = "";
        }
        document.cookie = name + "=" + value + expires + "; path=/; SameSite=Lax;";
    };
 
    context.readCookie = function(name) 
    {
        const nameEQ = name + "=";
        const ca = document.cookie.split(';');
        for (let i = 0; i < ca.length; i++) 
        {
            const c = ca[i];
            while (c.charAt(0) == ' ') 
            {
                c = c.substring(1, c.length);
            }
            if (c.indexOf(nameEQ) == 0) 
            {
                return c.substring(nameEQ.length, c.length);
            }
        }
        return null;
    };

    context.eraseCookie = function(name) 
    {
        context.createCookie(name, "", -1);
    };
})(WriteupFeedFilter.CookieUtils);


// ===============================================================================================

WriteupFeedFilter.Modal = {};
(function(context) 
{ 
    context.show_modal = function(modal_id, title, html_body, modal_action)
    {
        const modal = $(`#${modal_id}`);
        modal.find(".modal_action").unbind();
        modal.find(".modal-title").text(title);
        modal.find(".modal-body").html(html_body);
        if (modal_action)
        {
            modal.find(".modal_action").click(async function()
            { 
                await modal_action(modal)
            });
        }
        modal.modal('show');
    }
})(WriteupFeedFilter.Modal);

// ===============================================================================================

WriteupFeedFilter.Database = {};
(function(context) 
{
    const constants = WriteupFeedFilter.Constants;
    const db = firebase.database();

    const path_to_ctf_names = function(uid) 
    {
        return constants.PATH_TO_CTF_NAMES.replace(constants.UID_PLACEHOLDER, uid);
    }

    const path_to_user_data = function(uid) 
    {
        return constants.PATH_TO_USER_DATA.replace(constants.UID_PLACEHOLDER, uid);
    }

    context.get_ctf_names = async function(uid)
    {
        const snapshot = await db.ref(path_to_ctf_names(uid)).once('value');
        const ctf_names = snapshot.val()?.split(constants.ENTRY_SEPARATOR) || [];
        ctf_names.length = Math.min(ctf_names.length, constants.MAX_CTF_ENTRIES); 
        return ctf_names;
    }

    context.set_ctf_names = async function(uid, ctf_names_arr)
    {
        const new_ctf_names = ctf_names_arr.join(constants.ENTRY_SEPARATOR);
        const ref = db.ref(path_to_user_data(uid));
        await ref.child(constants.KEY_USER_CTF_NAMES).set(new_ctf_names);
    }

    context.delete_user_data = async function(uid)
    {
        await db.ref(path_to_user_data(uid)).remove();
    }
})(WriteupFeedFilter.Database);


// ===============================================================================================

firebase.auth().onAuthStateChanged((user) => {
    if (user) 
    {
        // User is signed in

        $( "#nav_link_logout" ).click(function() 
        {
            firebase.auth().signOut().then(function() 
            {
                WriteupFeedFilter.CookieUtils.eraseCookie(WriteupFeedFilter.Constants.COOKIE_MENU_TYPE);
                setTimeout(function()
                {
                    // W/A: Refresh to reflect logout unless redirection kicked in first
                    window.location.reload();
                }, 100);
            }).catch(function(error) 
            {
                console.log(error);
            });
        });
        WriteupFeedFilter.CookieUtils.createCookie(WriteupFeedFilter.Constants.COOKIE_MENU_TYPE, 
                                                   WriteupFeedFilter.Constants.COOKIE_MENU_TYPE_LOGGED_IN, 
                                                   0);
    }
    else
    {
        WriteupFeedFilter.CookieUtils.eraseCookie(WriteupFeedFilter.Constants.COOKIE_MENU_TYPE);
    }
});

// ===============================================================================================

if ($("body").data("page-id") == WriteupFeedFilter.Constants["PageIds.FILTER"]) 
{
    firebase.auth().onAuthStateChanged(async (user) => 
    {
        if (!user) 
        {
            document.location.href = "/login";
            return;
        }

        // User is signed in

        $("#filter").show();

        //
        // --- Setup UI ---
        //

        //
        // RSS Feed Link
        //

        $("#rss_feed").val(`${window.location.origin}/writeups/${user.uid}`);
        $("#copy_rss_feed_link").click(function()
        {
            const copyText = document.getElementById("rss_feed");
            copyText.select();
            copyText.setSelectionRange(0, $(copyText).val().length); // For mobile devices
            document.execCommand("copy");
        }).popover({ trigger: "manual", placement: "top" })
        .click(function() 
        { 
            var pop = $(this); 
            pop.popover("show") 
            pop.on('shown.bs.popover', function() 
            { 
                setTimeout(function() 
                {
                    pop.popover("hide")
                }, 1000); 
            });
        });

        //
        // CTF Names List Entry Template
        //

        const create_input_wrapper = function()
        { 
            const input_wrapper = $(`
            <div class="input-group mb-3 ctf_name_entry">
                <input type="text" class="form-control ctf_name_input" 
                        maxlength="${WriteupFeedFilter.Constants.MAX_ENTRY_NAME_LEN}"
                        placeholder="CTF Name" aria-label="CTF Name" aria-describedby="basic-addon2">
                <div class="input-group-append">
                    <button class="btn btn-outline-secondary btn-danger 
                        text-white remove_ctf_name" type="button">&times;</button>
                </div>
            </div>`);
            input_wrapper.find(".remove_ctf_name").click(function()
            {
                input_wrapper.remove(); 
                show_hide_add_button();
            });
            return input_wrapper;
        };

        //
        // Add Button
        //

        const ctf_names_wrapper = $("#ctf_names_wrapper");
        const add_button = $('#add_button');
        add_button.click(function()
        {
            const input_wrapper = create_input_wrapper();
            $("#ctf_names").append(input_wrapper);
            
            show_hide_add_button();
            
            ctf_names_wrapper.scrollTop(ctf_names_wrapper.prop("scrollHeight"));
        });

        const show_hide_add_button = function() 
        {
            ($(".ctf_name_input").length < WriteupFeedFilter.Constants.MAX_CTF_ENTRIES) ? add_button.show() : add_button.hide();   
        };

        //
        // Save Button
        //

        $('#save_button').click(async function()
        {
            const ctf_names_arr = [];
            $(".ctf_name_entry").each(function(index, elem) 
            {
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

            try
            {
                await WriteupFeedFilter.Database.set_ctf_names(user.uid, ctf_names_arr);
            }
            catch (err)
            {
                console.log(err);
                WriteupFeedFilter.Modal.show_modal( "modal_error", "Error", 
                    "An error ocurred while trying to save your changes.");
                return;
            }

            WriteupFeedFilter.Modal.show_modal( "modal_success", "Changes Saved", 
                "Your changes were saved successfully. Your feed will reflect them automatically.");
        })
        .show();


        //
        // --- Fetch and show CTF names ---
        //

        try
        {
            const ctf_names = await WriteupFeedFilter.Database.get_ctf_names(user.uid);
            $("#ajax_loader").hide();

            ctf_names.forEach(ctf_name => 
            {
                const input_wrapper = create_input_wrapper();
                input_wrapper.find(".ctf_name_input").val(ctf_name);
                $("#ctf_names").append(input_wrapper);
            });

            if (ctf_names.length == 0)
            {
                $("#ctf_names").append(create_input_wrapper());
            }

            show_hide_add_button();
        }
        catch (err)
        {
            console.log(err);
            $("#ajax_loader").hide();
            WriteupFeedFilter.Modal.show_modal( "modal_error", "Error", 
                "An error ocurred while trying to retrieve your data.");
        }
    });
}

// ===============================================================================================

if ($("body").data("page-id") == WriteupFeedFilter.Constants["PageIds.LOGIN"]) 
{
    firebase.auth().onAuthStateChanged((user) => 
    {
        if (user) 
        {
            document.location.href = "/filter";
            return;
        } 

        var uiConfig = 
        {
            callbacks: 
            {
                signInSuccessWithAuthResult: function(authResult, redirectUrl) 
                {
                    // User successfully signed in.
                    // Return type determines whether we continue the redirect automatically (true)
                    // or whether we leave that to developer to handle (false).
                    WriteupFeedFilter.CookieUtils.createCookie(WriteupFeedFilter.Constants.COOKIE_MENU_TYPE, 
                                                                WriteupFeedFilter.Constants.COOKIE_MENU_TYPE_LOGGED_IN, 
                                                                0);
                    return true;
                },
                uiShown: function() 
                {
                    // The widget is rendered.
                    $(".firebaseui-title").text("Sign in / Sign up with email");
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
        
    });
}

// ===============================================================================================

if ($("body").data("page-id") == WriteupFeedFilter.Constants["PageIds.SETTINGS"]) 
{
    firebase.auth().onAuthStateChanged((user) => 
    {
        if (!user) 
        {
            document.location.href = "/login";
            return;
        }

        // User is signed in

        $("#user_email").val(user.email);

        const sanitize_html = function(html) 
        {
            return $('<div>').text(html).html()
        }

        $("#update_password").click(async function()
        {
            const current_password  = $("#current_password").val();
            const new_password_1    = $("#new_password_1").val();
            const new_password_2    = $("#new_password_2").val();

            try
            {
                if (current_password == "")
                {
                    throw "Please enter current password";
                }

                if (new_password_1 == "")
                {
                    throw "Please enter new password";
                }

                if (new_password_1 != new_password_2)
                {
                    throw "New passwords don't match";
                }

                const cred = firebase.auth.EmailAuthProvider.credential(user.email, current_password);

                try 
                {
                    await user.reauthenticateWithCredential(cred);
                }
                catch (err)
                {
                    console.log(err);
                    throw `An error has occurred. <br/>${sanitize_html(err.message)}`;
                }

                try 
                {
                    await user.updatePassword(new_password_1);
                }
                catch (err)
                {
                    console.log(err);
                    throw `An error has occurred. <br/>${sanitize_html(err.message)}`;
                }

                WriteupFeedFilter.Modal.show_modal("modal_success", "Password Updated", 
                                                    "<p>Your password was updated successfully!</p>");
                    
            }
            catch (err)
            {
                WriteupFeedFilter.Modal.show_modal("modal_error", "Error", `<p>${err}</p>`);
            }
        });

        $("#delete_account").click(function() 
        {
            const confirm_action_func = async function(modal) 
            {
                try
                {
                    const current_password = $("#confirm_password_delete_account").val();

                    if (current_password == "")
                    {
                        throw "In order to delete your account you must re-enter your current password";
                    }

                    const cred = firebase.auth.EmailAuthProvider.credential(user.email, current_password);

                    try 
                    {
                        await user.reauthenticateWithCredential(cred);
                    }
                    catch (err)
                    {
                        console.log(err);
                        throw `An error has occurred. <br/>${sanitize_html(err.message)}`;
                    }

                    try
                    {
                        await WriteupFeedFilter.Database.delete_user_data(user.uid);
                    }
                    catch (err)
                    {
                        console.log(err);
                        throw `An error has occurred. <br/>${sanitize_html(err.message)}`;
                    }
                    
                    try 
                    {
                        await user.delete();
                    }
                    catch (err)
                    {
                        console.log(err);
                        throw `An error has occurred. <br/>${sanitize_html(err.message)}`;
                    }
                }
                catch(err)
                {
                    modal.modal('hide');
                    WriteupFeedFilter.Modal.show_modal("modal_error", "Error", `<p>${err}</p>`);
                    return;
                }

                // User will be logged out

            }

            WriteupFeedFilter.Modal.show_modal( "modal_confirm", "Are you sure?", 
                        `<p>Deleting your account cannot be undone. You'll also lose your custom feed. 
                        <br/>To permanently delete your account, enter your password and click "Confirm".</p>
                        <input type='password' id='confirm_password_delete_account'/>`, confirm_action_func);
        });
    });
}

// ===============================================================================================