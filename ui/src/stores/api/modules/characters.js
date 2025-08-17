import { charactersApi } from "../characters.js";

export const charactersModule = {
  state: () => ({
    characters: [],
    currentCharacter: null,
    currentCharacterAudio: null,
    loading: false,
    error: null,
  }),

  getters: {
    getCurrentCharacter: (state) => {
      return state.characters.find((char) => char.is_current) || null;
    },
  },

  actions: {
    async fetchCharacters() {
      try {
        this.loading = true;
        this.error = null;

        const data = await charactersApi.fetchCharacters();
        this.characters = data;

        const currentChar = this.getCurrentCharacter;
        this.currentCharacter = currentChar?.name || null;

        return data;
      } catch (error) {
        this.error = error.response?.data?.detail || error.message;
        throw error;
      } finally {
        this.loading = false;
      }
    },

    async setCharacter(characterName) {
      try {
        this.loading = true;
        this.error = null;

        const data = await charactersApi.setCharacter(characterName);

        // 更新本地状态
        this.characters.forEach((char) => {
          char.is_current = char.name === characterName;
        });
        this.currentCharacter = characterName;
        this.currentCharacterAudio = data.audio_text;

        return data;
      } catch (error) {
        this.error = error.response?.data?.detail || error.message;
        throw error;
      } finally {
        this.loading = false;
      }
    },

    clearError() {
      this.error = null;
    },
  },
}; 