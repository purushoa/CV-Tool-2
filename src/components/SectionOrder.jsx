
import React from "react";

import {
  DndContext,
  closestCenter,
  PointerSensor,
  KeyboardSensor,
  useSensor,
  useSensors
} from "@dnd-kit/core";

import {
  SortableContext,
  sortableKeyboardCoordinates,
  verticalListSortingStrategy,
  useSortable,
  arrayMove
} from "@dnd-kit/sortable";

import { CSS } from "@dnd-kit/utilities";

import {
  GripVertical,
  RotateCcw
} from "lucide-react";

import {
  sectionLabels,
  getSectionOrder,
  defaultSectionOrder
} from "../utils/sectionOrder";

function SortableSection({
  id,
  index,
  hidden
}) {
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
    isDragging
  } = useSortable({ id });

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    touchAction: "none",
    position: "relative",
    zIndex: isDragging ? 50 : 1
  };

  return (
    <div
      ref={setNodeRef}
      style={style}
      {...attributes}
      {...listeners}
      className={`
        flex items-center gap-3
        rounded-xl border p-4
        select-none
        ${
          isDragging
            ? "cursor-grabbing border-blue-500 bg-blue-100 shadow-xl"
            : "cursor-grab border-slate-200 bg-white hover:border-blue-400 hover:bg-blue-50"
        }
      `}
    >
      <GripVertical
        size={22}
        className="shrink-0 text-slate-400"
      />

      <span className="text-sm text-slate-400">
        {index + 1}
      </span>

      <span className="flex-1 text-sm font-semibold text-slate-800">
        {sectionLabels[id]}
      </span>

      {hidden && (
        <span className="rounded-full bg-slate-100 px-2 py-1 text-xs text-slate-500">
          Hidden
        </span>
      )}

      <span className="text-xs text-slate-400">
        Drag to move
      </span>
    </div>
  );
}

export default function SectionOrder({
  cv,
  onChange
}) {
  const order = getSectionOrder(cv);

  const sensors = useSensors(
    useSensor(PointerSensor, {
      activationConstraint: {
        distance: 5
      }
    }),

    useSensor(KeyboardSensor, {
      coordinateGetter:
        sortableKeyboardCoordinates
    })
  );

  function handleDragEnd(event) {
    const { active, over } = event;

    if (!over || active.id === over.id) {
      return;
    }

    const oldIndex = order.indexOf(active.id);
    const newIndex = order.indexOf(over.id);

    if (oldIndex < 0 || newIndex < 0) {
      return;
    }

    const newOrder = arrayMove(
      order,
      oldIndex,
      newIndex
    );

    onChange(newOrder);
  }

  return (
    <div className="rounded-2xl border border-blue-200 bg-blue-50 p-4">

      {/* HEADER */}

      <div className="mb-4 flex flex-wrap items-center justify-between gap-3">

        <h3 className="font-bold text-slate-900">
          Reorder CV Sections
        </h3>

        <button
          type="button"
          onClick={() =>
            onChange([...defaultSectionOrder])
          }
          className="flex items-center gap-2 rounded-xl border border-slate-200 bg-white px-4 py-2 text-sm font-semibold text-slate-600 hover:bg-slate-100"
        >
          <RotateCcw size={15} />
          Reset order
        </button>

      </div>

      <p className="mb-4 text-sm text-slate-600">
        Click and hold any section, then drag it
        up or down to change its position in
        your CV.
      </p>

      {/* DRAG AND DROP SYSTEM */}

      <DndContext
        sensors={sensors}
        collisionDetection={closestCenter}
        onDragEnd={handleDragEnd}
      >
        <SortableContext
          items={order}
          strategy={verticalListSortingStrategy}
        >
          <div className="space-y-3">

            {order.map((id, index) => (
              <SortableSection
                key={id}
                id={id}
                index={index}
                hidden={
                  cv.selected?.[id] === false
                }
              />
            ))}

          </div>
        </SortableContext>
      </DndContext>

      <p className="mt-4 text-xs text-slate-500">
        Your CV preview updates automatically
        when you change the section order.
      </p>

    </div>
  );
}
