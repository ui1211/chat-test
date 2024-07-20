<template>
    <div>
      <div v-for="message in messages" :key="message">{{ message }}</div>
      <input v-model="message" @keyup.enter="sendMessage" placeholder="Type a message"/>
    </div>
  </template>
  
  <script>
  export default {
    data() {
      return {
        message: '',
        messages: [],
        websocket: null,
      };
    },
    mounted() {
      this.websocket = new WebSocket('ws://localhost:8000/ws/1');
  
      this.websocket.onmessage = (event) => {
        this.messages.push(event.data);
      };
    },
    methods: {
      sendMessage() {
        if (this.message.trim() !== '') {
          this.websocket.send(this.message);
          this.message = '';
        }
      },
    },
  };
  </script>
  