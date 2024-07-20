<template>
    <div>
      <div v-if="!inRoom">
        <input v-model="playerName" placeholder="Enter your name" />
        <button @click="createRoom">Create Room</button>
        <input v-model="roomNumber" placeholder="Enter room number" />
        <button @click="joinRoom">Join Room</button>
      </div>
      <div v-else>
        <div>Room Number: {{ roomNumber }}</div>
        <div v-for="message in messages" :key="message">{{ message }}</div>
        <input v-model="message" @keyup.enter="sendMessage" placeholder="Type a message"/>
      </div>
    </div>
  </template>
  
  <script>
  export default {
    data() {
      return {
        playerName: '',
        roomNumber: '',
        message: '',
        messages: [],
        websocket: null,
        inRoom: false,
      };
    },
    methods: {
      async createRoom() {
        const response = await fetch('http://localhost:8000/create_room');
        const data = await response.json();
        this.roomNumber = data.room_number;
        this.joinRoom();
      },
      joinRoom() {
        if (this.roomNumber && this.playerName) {
          this.websocket = new WebSocket(`ws://localhost:8000/ws/${this.roomNumber}/${this.playerName}`);
          this.websocket.onmessage = (event) => {
            this.messages.push(event.data);
          };
          this.inRoom = true;
        } else {
          alert("Please enter a room number and your name");
        }
      },
      sendMessage() {
        if (this.message.trim() !== '') {
          this.websocket.send(this.message);
          this.message = '';
        }
      },
    },
  };
  </script>
  