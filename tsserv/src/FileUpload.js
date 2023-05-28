import React, { useState } from 'react';
import axios from 'axios';
import './FileUpload.css';

function UploadFile() {
  const [file, setFile] = useState(null);
  const [uploaded, setUploaded] = useState(false);

  const handleFileUpload = (event) => {
    setFile(event.target.files[0]);
  }

  const handleUpload = async () => {
    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await axios.post('http://127.0.0.1:5000/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      });

      console.log(response.data);
      setUploaded(true);
    } catch (error) {
      console.error(error);
    }
  }

  return (
    <div class="container">
      <div class="upload-form">
        <label for="file-input">Choose a file to upload:</label>
        <input id="file-input" type="file" accept="audio/*,video/*" onChange={handleFileUpload} />
        <button id="upload-button" onClick={handleUpload}>Upload</button>
        {uploaded && <p>File uploaded successfully!</p>}
      </div>
    </div>
  );
}

export default UploadFile;