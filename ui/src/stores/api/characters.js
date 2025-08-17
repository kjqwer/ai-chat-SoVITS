import { api } from "./core.js";

export const charactersApi = {
  // 获取角色列表
  async fetchCharacters() {
    const response = await api.get("/characters");
    return response.data;
  },

  // 设置当前角色
  async setCharacter(characterName) {
    const response = await api.post(
      `/characters/set?character_name=${encodeURIComponent(characterName)}`
    );
    return response.data;
  },
}; 