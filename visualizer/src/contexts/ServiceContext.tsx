import React, { createContext, PropsWithChildren, useContext } from 'react';
import { GraphService, GraphServiceImpl } from '../services/GraphService';
import { DocService, DocServiceImpl } from '../services/DocService';
import { EntityService, EntityServiceImpl } from '../services/EntityService';
import {
  RelationService,
  RelationServiceImpl,
} from '../services/RelationService';
import {
  CooccurrenceService,
  CooccurrenceServiceImpl,
} from '../services/CooccurrenceService';

interface Services {
  graphService: GraphService;
  docService: DocService;
  entityService: EntityService;
  cooccurrenceService: CooccurrenceService;
  relationService: RelationService;
}

const ServiceContext = createContext<Services | undefined>(undefined);

export const ServiceContextProvider: React.FC<PropsWithChildren> = ({
  children,
}) => {
  const value: Services = {
    graphService: new GraphServiceImpl('http://localhost:8001'),
    docService: new DocServiceImpl('http://localhost:8001'),
    entityService: new EntityServiceImpl('http://localhost:8001'),
    cooccurrenceService: new CooccurrenceServiceImpl('http://localhost:8001'),
    relationService: new RelationServiceImpl('http://localhost:8001'),
  };

  return (
    <ServiceContext.Provider value={value}>{children}</ServiceContext.Provider>
  );
};

export const useServiceContext = (): Services => {
  const context = useContext(ServiceContext);
  if (!context) {
    throw new Error('useServiceContext must be used within a ServiceProvider');
  }
  return context;
};
