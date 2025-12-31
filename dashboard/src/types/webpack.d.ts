// Webpack Module Federation type definitions
declare global {
  interface Window {
    [key: string]: any;
  }
  
  function __webpack_init_sharing__(scope: string): Promise<void>;
  const __webpack_share_scopes__: {
    default: Record<string, any>;
  };
}

export {};

