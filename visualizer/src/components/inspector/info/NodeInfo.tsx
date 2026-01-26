import React from 'react';
import { Node } from '../../../types/graph';
import { Panel } from '../../common/Panel';
import { EntityInfo } from './EntityInfo';

interface SubnodeListProps {
  subnodes: Node[];
}

export const SubnodeList: React.FC<SubnodeListProps> = ({ subnodes }) => {
  if (subnodes.length === 0) return null;

  return (
    <details>
      <summary>Subnodes</summary>
      {subnodes.map((subnode, index) => (
        <div key={subnode.id}>
          <b>{subnode.label}</b>
          <EntityInfo id={subnode.id} />
          {index + 1 < subnodes.length && <hr />}
        </div>
      ))}
    </details>
  );
};

export interface NodeInfoProps {
  node: Node;
}

export const NodeInfo: React.FC<NodeInfoProps> = ({ node }) => {
  return (
    <Panel className="info-pane">
      <h2>{node.label}</h2>
      {node.supernode && <p>Supernode: {node.supernode.label}</p>}

      <EntityInfo id={node.id} />

      {node.subnodes && node.subnodes.length > 0 && (
        <>
          <br />
          <SubnodeList subnodes={node.subnodes} />
        </>
      )}
    </Panel>
  );
};
