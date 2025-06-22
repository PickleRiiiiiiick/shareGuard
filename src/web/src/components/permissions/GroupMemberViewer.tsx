import React, { useState } from 'react';
import { ChevronRightIcon, ChevronDownIcon, UserIcon, UserGroupIcon } from '@heroicons/react/24/outline';
import { useGroupMembers } from '@/hooks/useFolders';
import { LoadingSpinner } from '@components/common/LoadingSpinner';
import type { GroupMembersInfo, GroupMember } from '@/api/folders';

interface GroupMemberViewerProps {
  groupName: string;
  domain: string;
  onClose?: () => void;
}

interface ExpandedState {
  [key: string]: boolean;
}

export function GroupMemberViewer({ groupName, domain, onClose }: GroupMemberViewerProps) {
  const [expanded, setExpanded] = useState<ExpandedState>({});
  const [selectedMember, setSelectedMember] = useState<string | null>(null);
  
  const { data: groupData, isLoading, error } = useGroupMembers(
    groupName,
    domain,
    true,
    { enabled: !!groupName && !!domain }
  );

  const toggleExpanded = (key: string) => {
    setExpanded(prev => ({
      ...prev,
      [key]: !prev[key]
    }));
  };

  const handleMemberClick = (member: GroupMember) => {
    setSelectedMember(member.full_name);
  };

  const renderMember = (member: GroupMember, depth: number = 0, parentKey: string = '') => {
    const key = `${parentKey}-${member.full_name}`;
    const isGroup = member.type.toLowerCase().includes('group') || member.type.toLowerCase() === 'alias';
    const isSelected = selectedMember === member.full_name;
    
    return (
      <div
        key={key}
        className={`flex items-center gap-2 py-2 px-3 rounded-md cursor-pointer transition-colors ${
          isSelected 
            ? 'bg-blue-100 border border-blue-300' 
            : 'hover:bg-gray-50'
        }`}
        style={{ marginLeft: `${depth * 20}px` }}
        onClick={() => handleMemberClick(member)}
      >
        {isGroup ? (
          <UserGroupIcon className="h-4 w-4 text-blue-600" />
        ) : (
          <UserIcon className="h-4 w-4 text-gray-600" />
        )}
        
        <div className="flex-1">
          <div className="flex items-center gap-2">
            <span className={`text-sm font-medium ${isSelected ? 'text-blue-900' : 'text-gray-900'}`}>
              {member.name}
            </span>
            <span className={`text-xs px-2 py-0.5 rounded-full ${
              isGroup 
                ? 'bg-blue-100 text-blue-800' 
                : 'bg-gray-100 text-gray-600'
            }`}>
              {member.type}
            </span>
          </div>
          <div className="text-xs text-gray-500">
            {member.domain}\\{member.name}
          </div>
        </div>
      </div>
    );
  };

  const renderGroupTree = (groupInfo: GroupMembersInfo, depth: number = 0, parentKey: string = '') => {
    const groupKey = `${parentKey}-group-${groupInfo.full_name}`;
    const isExpanded = expanded[groupKey];
    const hasNestedGroups = groupInfo.nested_groups && groupInfo.nested_groups.length > 0;

    return (
      <div key={groupKey} className="space-y-1">
        {/* Group Header */}
        <div
          className="flex items-center gap-2 py-2 px-3 bg-blue-50 rounded-md border border-blue-200 cursor-pointer"
          style={{ marginLeft: `${depth * 20}px` }}
          onClick={() => toggleExpanded(groupKey)}
        >
          {hasNestedGroups && (
            isExpanded ? (
              <ChevronDownIcon className="h-4 w-4 text-blue-600" />
            ) : (
              <ChevronRightIcon className="h-4 w-4 text-blue-600" />
            )
          )}
          <UserGroupIcon className="h-5 w-5 text-blue-600" />
          <div className="flex-1">
            <div className="flex items-center gap-2">
              <span className="text-sm font-semibold text-blue-900">
                {groupInfo.group_name}
              </span>
              <span className="text-xs bg-blue-200 text-blue-800 px-2 py-0.5 rounded-full">
                {groupInfo.total_direct_members} direct members
              </span>
              {groupInfo.total_all_members !== groupInfo.total_direct_members && (
                <span className="text-xs bg-green-200 text-green-800 px-2 py-0.5 rounded-full">
                  {groupInfo.total_all_members} total members
                </span>
              )}
            </div>
            <div className="text-xs text-blue-700">
              {groupInfo.domain}\\{groupInfo.group_name}
            </div>
          </div>
        </div>

        {/* Direct Members */}
        {groupInfo.direct_members && groupInfo.direct_members.length > 0 && (
          <div className="space-y-1">
            {groupInfo.direct_members.map((member, index) => 
              renderMember(member, depth + 1, `${groupKey}-direct-${index}`)
            )}
          </div>
        )}

        {/* Nested Groups */}
        {isExpanded && hasNestedGroups && (
          <div className="space-y-2">
            {groupInfo.nested_groups.map((nestedGroup, index) => 
              renderGroupTree(nestedGroup, depth + 1, `${groupKey}-nested-${index}`)
            )}
          </div>
        )}
      </div>
    );
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-48">
        <LoadingSpinner />
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-4 bg-red-50 border border-red-200 rounded-md">
        <p className="text-sm text-red-800">
          Error loading group members: {error instanceof Error ? error.message : String(error)}
        </p>
      </div>
    );
  }

  if (!groupData?.group_info) {
    return (
      <div className="p-4 bg-gray-50 border border-gray-200 rounded-md">
        <p className="text-sm text-gray-600">
          No group information available
        </p>
      </div>
    );
  }

  const { group_info } = groupData;

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h4 className="text-lg font-semibold text-gray-900">
            Group Members: {group_info.group_name}
          </h4>
          <p className="text-sm text-gray-500">
            {group_info.domain}\\{group_info.group_name}
          </p>
        </div>
        {onClose && (
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 p-1"
          >
            ✕
          </button>
        )}
      </div>

      {/* Summary Stats */}
      <div className="flex gap-4 p-3 bg-gray-50 rounded-lg">
        <div className="text-center">
          <div className="text-xl font-bold text-blue-600">
            {group_info.total_direct_members}
          </div>
          <div className="text-xs text-gray-600">Direct Members</div>
        </div>
        <div className="text-center">
          <div className="text-xl font-bold text-green-600">
            {group_info.total_all_members}
          </div>
          <div className="text-xs text-gray-600">Total Members</div>
        </div>
        <div className="text-center">
          <div className="text-xl font-bold text-purple-600">
            {group_info.nested_groups?.length || 0}
          </div>
          <div className="text-xs text-gray-600">Nested Groups</div>
        </div>
      </div>

      {/* Group Tree */}
      <div className="border rounded-lg p-4 bg-white max-h-96 overflow-y-auto">
        {group_info.error ? (
          <div className="p-4 bg-red-50 border border-red-200 rounded-md">
            <p className="text-sm text-red-800">{group_info.error}</p>
          </div>
        ) : (
          renderGroupTree(group_info)
        )}
      </div>

      {/* Selected Member Details */}
      {selectedMember && (
        <div className="p-3 bg-blue-50 border border-blue-200 rounded-lg">
          <h5 className="text-sm font-medium text-blue-900 mb-1">
            Selected Member
          </h5>
          <p className="text-sm text-blue-800">{selectedMember}</p>
        </div>
      )}
    </div>
  );
}