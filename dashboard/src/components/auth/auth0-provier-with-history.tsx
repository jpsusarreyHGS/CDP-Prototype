import React, { useEffect } from 'react';
import { Auth0Provider, useAuth0 } from '@auth0/auth0-react';

import config from '../../config';
import { FEATURE_TOGGLES, apiUrls } from '../../constants';

export let currentUserToken: string | null = null;
export let idtoken: string | null = null;
export let userInfo: any = {}; // Adjust the type as per your user information structure

function GetCurrentUserAccessToken() {
  const { user, getAccessTokenSilently, getIdTokenClaims } = useAuth0();

  useEffect(() => {
    const getUserMetadata = async () => {
      try {
        if (currentUserToken === null && getAccessTokenSilently) {
          const accessToken = await getAccessTokenSilently();
          userInfo = user;
          currentUserToken = accessToken;
          const idTokenClaims = await getIdTokenClaims();
          if (idTokenClaims?.__raw) {
            idtoken = idTokenClaims?.__raw;
          }
        }
      } catch (e: any) {
        console.error('Auth0 error:', e.message);
      }
    };

    getUserMetadata();
  }, [getAccessTokenSilently, getIdTokenClaims, user?.sub]);

  return null;
}

interface Auth0ProviderWithHistoryProps {
  children: React.ReactNode;
}

const Auth0ProviderWithHistory: React.FC<Auth0ProviderWithHistoryProps> = ({
  children,
}) => {
  let providerConfig: any = {};

  if (FEATURE_TOGGLES.ENABLE_AUTH0_ORGANIZATION) {
    providerConfig = {
      clientId: apiUrls.AUTH0_ORGANIZATIONS_CLIENT_ID,
      domain: apiUrls.AUTH0_ORGANIZATIONS_DOMAIN,
      authorizationParams: {
        organization: apiUrls.AUTH0_ORGANIZATIONS_ID,
        redirect_uri: window.location.origin,
        ...(apiUrls.AUTH0_ORGANIZATIONS_AUDIENCE
          ? { audience: apiUrls.AUTH0_ORGANIZATIONS_AUDIENCE }
          : null),
      },
    };
  } else {
    providerConfig = {
      domain: config.AUTH0_DOMAIN,
      clientId: config.AUTH0_CLIENT_ID,
      authorizationParams: {
        redirect_uri: window.location.origin,
        ...(config.AUTH0_AUDIENCE ? { audience: config.AUTH0_AUDIENCE } : null),
      },
    };
  }
  if (FEATURE_TOGGLES.ENABLE_AUTH0_LOCAL_STORAGE_USAGE) {
    providerConfig.cacheLocation = 'localstorage';
  }

  // If Auth0 is not configured, render children without Auth0Provider
  if (!providerConfig.domain || !providerConfig.clientId) {
    console.warn('Auth0 is not configured. Running without authentication.');
    return <>{children}</>;
  }

  return (
    <Auth0Provider {...providerConfig}>
      <GetCurrentUserAccessToken />
      {children}
    </Auth0Provider>
  );
};

export default Auth0ProviderWithHistory;
