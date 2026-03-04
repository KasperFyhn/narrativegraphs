import React, {
  createContext,
  type ReactNode,
  useContext,
  useEffect,
  useState,
} from 'react';
import { Community } from '../types/graph';
import {
  CommunitiesRequest,
  CommunityDetectionMethod,
  WeightMeasure,
} from '../types/graphQuery';

const DEFAULT_REQUEST: CommunitiesRequest = {
  weightMeasure: 'pmi' as WeightMeasure,
  minWeight: 0.0,
  communityDetectionMethod: 'louvain' as CommunityDetectionMethod,
  communityDetectionMethodArgs: {},
};

export interface CommunitiesContextType {
  communities: Community[] | null;
  setCommunities: (communities: Community[] | null) => void;
  commRequest: CommunitiesRequest;
  setCommRequest: (request: CommunitiesRequest) => void;
  showIsolated: boolean;
  setShowIsolated: (show: boolean) => void;
}

const CommunitiesContext = createContext<CommunitiesContextType | undefined>(
  undefined,
);

interface CommunitiesContextProviderProps {
  children: ReactNode;
}

export const CommunitiesContextProvider: React.FC<
  CommunitiesContextProviderProps
> = ({ children }) => {
  const [communities, setCommunities] = useState<Community[] | null>([]);
  const [commRequest, setCommRequest] =
    useState<CommunitiesRequest>(DEFAULT_REQUEST);
  const [showIsolated, setShowIsolated] = useState(true);

  useEffect(() => {
    setCommunities([]);
  }, [commRequest]);

  return (
    <CommunitiesContext.Provider
      value={{
        communities,
        setCommunities,
        commRequest,
        setCommRequest,
        showIsolated,
        setShowIsolated,
      }}
    >
      {children}
    </CommunitiesContext.Provider>
  );
};

export const useCommunitiesContext = (): CommunitiesContextType => {
  const context = useContext(CommunitiesContext);
  if (!context) {
    throw new Error(
      'useCommunitiesContext must be used within a CommunitiesContextProvider',
    );
  }
  return context;
};
