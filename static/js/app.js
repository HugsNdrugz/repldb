document.addEventListener('DOMContentLoaded', function() {
    feather.replace();

    const sidebarLinks = document.querySelectorAll('.sidebar nav ul li');
    const sections = document.querySelectorAll('.section');
    const chatWindow = document.querySelector('.chat-window');
    const closeChatBtn = document.querySelector('.close-chat');
    const smsWindow = document.querySelector('.sms-window');
    const closeSmsBtn = document.querySelector('.close-sms');
     const inspectorPanel = document.querySelector('.inspector');
    const closeInspectorBtn = document.querySelector('.close-inspector');
    const searchInputs = document.querySelectorAll('input[type="text"]');
    const fileUpload = document.getElementById('file-upload');
     const uploadProgress = document.getElementById('upload-progress');
     const uploadMessage = document.getElementById('upload-message');

     // Global variable to store data (for search and upload)
     let chatData = [];
    let callData = [];
    let keylogData = [];
    let contactData = [];
     let smsData = [];
    let appData = [];
    let currentPage = 1;
    let perPage = 10;

     // Generic function to fetch and load data
    async function fetchData(sectionId, page = 1, perPage = 10) {
      try {
          const response = await fetch(`/get_data?section=${sectionId}&page=${page}&per_page=${perPage}`);
          if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
           }
           return await response.json();
      } catch (error) {
          console.error(`Error loading data for ${sectionId}:`, error);
           return null;
      }
   }

     // Generic function to display data
    function displayData(sectionId, data) {
       const container = document.getElementById(`${sectionId}-list`) || document.querySelector(`#${sectionId}-table tbody`);

        if(!container){
            console.error(`Container not found for section: ${sectionId}`)
             return;
        }
         container.innerHTML = '';

        if (!data || data.length === 0){
           return;
        }

        if (sectionId === 'keylogs') {
             data.forEach(item => {
                const row = document.createElement('tr');
                 row.innerHTML = `
                      <td>${item.application}</td>
                       <td>${item.time}</td>
                      <td>${item.text}</td>
                   `;
                   container.appendChild(row);
            });
            return;
        }

        data.forEach(item => {
           const element = document.createElement('div');
           element.classList.add(`${sectionId.slice(0, -1)}-item`);

           let content;
              if(sectionId === 'chats' || sectionId === 'sms'){
                content = `
                     <img src="${item.profile_pic}" alt="${item.name}">
                    <div>
                        <h3>${item.name}</h3>
                        <p>${item.last_message}</p>
                    </div>
                 `;

                 element.addEventListener('click', () => {
                   if (sectionId === 'chats') {
                     openChatWindow(item.name, item.messages);
                    } else if (sectionId === 'sms') {
                       openSmsWindow(item.name, item.messages);
                    }
                });
              } else if (sectionId === 'calls') {
                content = `
                  <img src="${item.profile_pic}" alt="${item.name}">
                   <div>
                        <h3>${item.name}</h3>
                        <p>${item.time}</p>
                    </div>
                 `;
              }else if (sectionId === 'contacts') {
               content = `
                   <img src="${item.profile_pic}" alt="${item.name}">
                    <div>
                        <h3>${item.name}</h3>
                        <p>${item.phone_number}</p>
                    </div>
                  `;
                } else if(sectionId === 'installed_apps'){
                   content = `
                      <img src="${item.icon}" alt="${item.name}">
                     <div>
                        <h3>${item.name}</h3>
                         <p>${item.version}</p>
                     </div>
                    `;
                }

            element.innerHTML = content;
             container.appendChild(element);
         })
   }


    // Function to activate a section
    function activateSection(sectionId) {
        sections.forEach(section => section.classList.remove('active'));
        document.getElementById(sectionId).classList.add('active');
    }

     // Function to open chat window
     function openChatWindow(name, messages) {
        document.getElementById('chat-window-name').textContent = name;
        const chatMessages = document.getElementById('chat-messages');
         chatMessages.innerHTML = '';
        messages.forEach(message => {
            const messageDiv = document.createElement('div');
            messageDiv.classList.add('message');
            messageDiv.innerHTML = `
               <div class="sender">${message.sender}</div>
                <div class="content">${message.content}</div>
            `;
            chatMessages.appendChild(messageDiv);
        });
        chatWindow.classList.remove('hidden');
    }

    // Function to open sms window
    function openSmsWindow(name, messages) {
       document.getElementById('sms-window-name').textContent = name;
         const smsMessages = document.getElementById('sms-messages');
         smsMessages.innerHTML = '';
        messages.forEach(message => {
            const messageDiv = document.createElement('div');
           messageDiv.classList.add('message');
            messageDiv.innerHTML = `
               <div class="sender">${message.sender}</div>
               <div class="content">${message.content}</div>
           `;
            smsMessages.appendChild(messageDiv);
       });
         smsWindow.classList.remove('hidden');
    }


     // Function to load and display data
      async function loadData(sectionId, page = 1, perPage = 10) {
          const response = await fetchData(sectionId, page, perPage);
            if (response && response.data) {
                 if (sectionId === 'chats') {
                        chatData = response.data;
                    } else if (sectionId === 'calls') {
                        callData = response.data;
                     } else if (sectionId === 'keylogs') {
                         keylogData = response.data;
                     } else if (sectionId === 'contacts') {
                        contactData = response.data;
                    } else if (sectionId === 'sms') {
                        smsData = response.data;
                    } else if (sectionId === 'installed_apps') {
                        appData = response.data;
                    }
                displayData(sectionId, response.data);
                updateSearchResults(sectionId, '');
                // Update pagination info
                currentPage = response.page;
                perPage = response.per_page;
                const totalPages = response.total_pages;
                 updatePagination(sectionId, currentPage, totalPages);
            }
       }


    function updateSearchResults(sectionId, searchTerm) {
      let data;
       const resultsContainer = document.getElementById(`search-results-${sectionId}`);
        if (sectionId === 'chats') {
            data = chatData;
        } else if (sectionId === 'calls') {
            data = callData;
        } else if (sectionId === 'keylogs') {
            data = keylogData;
        } else if (sectionId === 'contacts') {
            data = contactData;
        } else if (sectionId === 'sms') {
           data = smsData;
        } else if (sectionId === 'installed_apps') {
            data = appData;
        }

        if (!data) {
          resultsContainer.innerHTML = '';
          resultsContainer.classList.remove('active');
          return;
         }

        const filteredData = data.filter(item => {
              if(item.name){
                   return item.name.toLowerCase().includes(searchTerm.toLowerCase())
              }
              if(item.application){
                 return item.application.toLowerCase().includes(searchTerm.toLowerCase())
              }
             return false;
            });

        resultsContainer.innerHTML = '';
         if (filteredData.length > 0 && searchTerm.trim() !== '') {
            resultsContainer.classList.add('active');
             filteredData.forEach(item => {
                 const resultDiv = document.createElement('div');
                 if(item.name){
                      resultDiv.textContent = item.name;
                     resultDiv.addEventListener('click', () => {
                         if (sectionId === 'chats') {
                              const selectedChat = chatData.find(chat => chat.name === item.name);
                             if(selectedChat){
                                openChatWindow(selectedChat.name, selectedChat.messages);
                             }
                          }
                            if (sectionId === 'sms') {
                              const selectedSms = smsData.find(sms => sms.name === item.name);
                             if(selectedSms){
                                openSmsWindow(selectedSms.name, selectedSms.messages);
                            }
                          }
                      });
                   }
                if(item.application){
                     resultDiv.textContent = item.application;
                  }
                 resultsContainer.appendChild(resultDiv);
            });
        }else{
           resultsContainer.classList.remove('active');
        }

   }

     // Function to update inspector details
      function updateInspector(element, x, y, width, height, fontFamily, fontSize, lineHeight, textAlign, letterSpacing, fill) {
        const inspectorTitle = document.getElementById('inspector-title');
         const widthDisplay = document.querySelector('.object-properties .size .width');
         const heightDisplay = document.querySelector('.object-properties .size .height');
          const fontFamilyDisplay = document.querySelector('.typeface .font-family');
        const fontSizeDisplay = document.querySelector('.typeface .font-size');
        const lineHeightDisplay = document.querySelector('.typeface .line-height');
        const textAlignDisplay = document.querySelector('.typeface .text-align');
        const letterSpacingDisplay = document.querySelector('.typeface .letter-spacing');
       const fillDisplay = document.querySelector('.colors .fill');

           inspectorTitle.textContent = element;
          widthDisplay.textContent = width;
          heightDisplay.textContent = height
           fontFamilyDisplay.textContent = fontFamily;
        fontSizeDisplay.textContent = fontSize;
        lineHeightDisplay.textContent = lineHeight;
        textAlignDisplay.textContent = textAlign;
        letterSpacingDisplay.textContent = letterSpacing;
         fillDisplay.textContent = fill;

          // Add any additional property if needed
        inspectorPanel.classList.remove('hidden');
     }
     function updatePagination(sectionId, currentPage, totalPages) {
        const paginationContainer = document.getElementById(`pagination-${sectionId}`);
        if (!paginationContainer) return;

        paginationContainer.innerHTML = '';

        if (totalPages <= 1) return;

        const prevButton = document.createElement('button');
        prevButton.textContent = 'Previous';
        prevButton.disabled = currentPage === 1;
        prevButton.addEventListener('click', () => {
            loadData(sectionId, currentPage - 1, perPage);
        });
        paginationContainer.appendChild(prevButton);

        const pageInfo = document.createElement('span');
        pageInfo.textContent = `Page ${currentPage} of ${totalPages}`;
        paginationContainer.appendChild(pageInfo);

        const nextButton = document.createElement('button');
        nextButton.textContent = 'Next';
        nextButton.disabled = currentPage === totalPages;
        nextButton.addEventListener('click', () => {
            loadData(sectionId, currentPage + 1, perPage);
        });
        paginationContainer.appendChild(nextButton);
    }

   // Load initial data based on the active section
      sections.forEach(section => {
            if (section.classList.contains('active')) {
                loadData(section.id);
           }
       });



    // Event listeners
    sidebarLinks.forEach(link => {
        link.addEventListener('click', async function(event) {
            event.preventDefault();
            const sectionId = this.getAttribute('data-section');
           activateSection(sectionId);
             await loadData(sectionId)
            inspectorPanel.classList.add('hidden')
        });
    });

      closeChatBtn.addEventListener('click', () => {
        chatWindow.classList.add('hidden');
    });
    closeSmsBtn.addEventListener('click', () => {
        smsWindow.classList.add('hidden');
    });
    closeInspectorBtn.addEventListener('click', () => {
        inspectorPanel.classList.add('hidden');
    });

    searchInputs.forEach(input => {
       input.addEventListener('input', function(){
          const sectionId = this.closest('.section').id;
          updateSearchResults(sectionId, this.value);
       })
    })

      // File Upload Handler
        fileUpload.addEventListener('change', async function(event) {
            const file = event.target.files[0];
             if (!file) return;

            const formData = new FormData();
            formData.append('file', file);

             uploadProgress.style.display = 'block';
              uploadMessage.textContent = 'Uploading...';

             const xhr = new XMLHttpRequest();
            xhr.open('POST', '/upload', true);
            xhr.upload.onprogress = function(e) {
               if (e.lengthComputable) {
                    const percentComplete = (e.loaded / e.total) * 100;
                    uploadProgress.value = percentComplete;
                }
            };

              xhr.onload = async function() {
                if (xhr.status === 200) {
                     uploadProgress.style.display = 'none';
                     uploadMessage.textContent = 'Upload successful!';
                     const response = JSON.parse(xhr.responseText);
                    if (response.reload_required) {
                           sections.forEach(section => {
                            if (section.classList.contains('active')) {
                                refreshData(section.id);
                           }
                       });
                   }
                } else {
                    uploadProgress.style.display = 'none';
                   uploadMessage.textContent = 'Upload failed.';
               }
           };

             xhr.onerror = function(){
                uploadProgress.style.display = 'none';
                  uploadMessage.textContent = 'Upload failed.';
             }
             xhr.send(formData);
        });

      // Function for refreshing data, handles refreshing specific sections
    window.refreshData = async function(sectionId) {
        await loadData(sectionId);
    }


        // Event listener for inspecting elements
        document.addEventListener('click', function(event) {
          const element = event.target.closest('.chat-item, .call-item, .sms-item, .contact-item, .app-item');
             if(element){
              let elementDetails = {};
               if (element.classList.contains('chat-item')) {
                    const chat = chatData.find(c => c.name === element.querySelector('h3').textContent);
                     elementDetails = {
                         element: 'chat',
                          x: 'auto',
                          y: 'auto',
                          width: 'auto',
                          height: 'auto',
                           fontFamily: 'Helvetica, Arial, sans-serif',
                           fontSize: '12px',
                          lineHeight: '16.08px',
                         textAlign: 'start',
                         letterSpacing: 'normal',
                         fill: '#65676b'
                        }
                  }  else if (element.classList.contains('call-item')) {
                       const call = callData.find(c => c.name === element.querySelector('h3').textContent);
                         elementDetails = {
                         element: 'call',
                           x: 'auto',
                           y: 'auto',
                           width: 'auto',
                          height: 'auto',
                         fontFamily: 'Helvetica, Arial, sans-serif',
                        fontSize: '12px',
                         lineHeight: '16.08px',
                        textAlign: 'start',
                       letterSpacing: 'normal',
                        fill: '#385898'
                       }
                  }  else if (element.classList.contains('sms-item')) {
                        const sms = smsData.find(s => s.name === element.querySelector('h3').textContent);
                         elementDetails = {
                           element: 'sms',
                            x: 'auto',
                            y: 'auto',
                           width: 'auto',
                           height: 'auto',
                           fontFamily: 'Helvetica, Arial, sans-serif',
                           fontSize: '12px',
                         lineHeight: '16.08px',
                           textAlign: 'start',
                           letterSpacing: 'normal',
                          fill: '#1c1e21'
                       }
                 }  else if (element.classList.contains('contact-item')) {
                         const contact = contactData.find(c => c.name === element.querySelector('h3').textContent);
                         elementDetails = {
                            element: 'contact',
                           x: '32',
                           y: '32',
                           width: '32px',
                            height: '32px',
                            fontFamily: 'Helvetica, Arial, sans-serif',
                            fontSize: '12px',
                            lineHeight: '16.08px',
                             textAlign: 'start',
                             letterSpacing: 'normal',
                           fill: '#1c1e21'
                        }
                } else if (element.classList.contains('app-item')) {
                        const app = appData.find(a => a.name === element.querySelector('h3').textContent);
                        elementDetails = {
                           element: 'app',
                            x: '20',
                            y: '20',
                           width: '20px',
                           height: '20px',
                             fontFamily: 'Helvetica, Arial, sans-serif',
                           fontSize: '12px',
                            lineHeight: '16.08px',
                            textAlign: 'start',
                            letterSpacing: 'normal',
                           fill: '#65676b'
                         }
                   }

                 updateInspector(elementDetails.element, elementDetails.x, elementDetails.y,  elementDetails.width, elementDetails.height,  elementDetails.fontFamily, elementDetails.fontSize, elementDetails.lineHeight, elementDetails.textAlign, elementDetails.letterSpacing, elementDetails.fill);
             }

       });
});