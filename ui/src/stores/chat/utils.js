// 合并模块状态的工具函数
export function mergeModuleStates(modules) {
  const mergedState = {};
  
  modules.forEach(module => {
    const moduleState = module.state();
    Object.assign(mergedState, moduleState);
  });
  
  return mergedState;
}

// 合并模块getters的工具函数
export function mergeModuleGetters(modules) {
  const mergedGetters = {};
  
  modules.forEach(module => {
    if (module.getters) {
      Object.assign(mergedGetters, module.getters);
    }
  });
  
  return mergedGetters;
}

// 合并模块actions的工具函数
export function mergeModuleActions(modules) {
  const mergedActions = {};
  
  modules.forEach(module => {
    if (module.actions) {
      Object.assign(mergedActions, module.actions);
    }
  });
  
  return mergedActions;
} 