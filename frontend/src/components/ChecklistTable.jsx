import React, { useState } from 'react';
import { Plus, Edit3, Trash2 } from 'lucide-react';

export default function ChecklistTable({ 
  tender, 
  requirements, 
  onAddRequirement, 
  onEditRequirement, 
  onDeleteRequirement,
  isApproved 
}) {
  const [selectedCategory, setSelectedCategory] = useState('ALL');
  
  // Dialog state
  const [isAddOpen, setIsAddOpen] = useState(false);
  const [isEditOpen, setIsEditOpen] = useState(false);
  const [isDeleteOpen, setIsDeleteOpen] = useState(false);

  // Form states
  const [editingReq, setEditingReq] = useState(null);
  const [deletingReqId, setDeletingReqId] = useState(null);

  const [formName, setFormName] = useState('');
  const [formCategory, setFormCategory] = useState('POLICY');
  const [formOperator, setFormOperator] = useState('>=');
  const [formValue, setFormValue] = useState('');
  const [formUnit, setFormUnit] = useState('%');
  const [formClause, setFormClause] = useState('');
  const [formPage, setFormPage] = useState('');

  const categories = ['ALL', 'POLICY', 'FINANCIAL', 'LEGAL', 'QUALITY', 'AUTHORIZATION', 'EXPERIENCE'];

  const filteredRequirements = selectedCategory === 'ALL'
    ? requirements
    : requirements.filter(r => r.category === selectedCategory);

  const handleOpenAdd = () => {
    setFormName('');
    setFormCategory('POLICY');
    setFormOperator('>=');
    setFormValue('50');
    setFormUnit('%');
    setFormClause('8.2');
    setFormPage('14');
    setIsAddOpen(true);
  };

  const handleSaveAdd = (e) => {
    e.preventDefault();
    if (!formName.trim()) return;

    const newReq = {
      requirement_id: `REQ_${Date.now().toString().slice(-4)}`,
      name: formName.trim(),
      category: formCategory,
      operator: formOperator,
      required_value: isNaN(Number(formValue)) ? formValue : Number(formValue),
      unit: formUnit.trim(),
      source: {
        clause: formClause.trim() || '1.0',
        page: Number(formPage) || 1
      },
      approved: true
    };

    onAddRequirement(tender.tender_id, newReq);
    setIsAddOpen(false);
  };

  const handleOpenEdit = (req) => {
    setEditingReq(req);
    setFormName(req.name);
    setFormCategory(req.category);
    setFormOperator(req.operator);
    setFormValue(req.required_value.toString());
    setFormUnit(req.unit);
    setFormClause(req.source.clause);
    setFormPage(req.source.page.toString());
    setIsEditOpen(true);
  };

  const handleSaveEdit = (e) => {
    e.preventDefault();
    if (!editingReq || !formName.trim()) return;

    const updatedReq = {
      ...editingReq,
      name: formName.trim(),
      category: formCategory,
      operator: formOperator,
      required_value: isNaN(Number(formValue)) ? formValue : Number(formValue),
      unit: formUnit.trim(),
      source: {
        clause: formClause.trim(),
        page: Number(formPage) || 1
      }
    };

    onEditRequirement(tender.tender_id, editingReq.requirement_id, updatedReq);
    setIsEditOpen(false);
    setEditingReq(null);
  };

  const handleOpenDelete = (reqId) => {
    setDeletingReqId(reqId);
    setIsDeleteOpen(true);
  };

  const handleConfirmDelete = () => {
    if (deletingReqId) {
      onDeleteRequirement(tender.tender_id, deletingReqId);
      setIsDeleteOpen(false);
      setDeletingReqId(null);
    }
  };

  const formatCondition = (req) => {
    return req.category;
  };

  return (
    <div className="space-y-5">
      {/* Category Filter Pills (Text Buttons) */}
      <div className="flex items-center justify-between pb-3 border-b border-[#E5E0DA]">
        <div className="flex items-center space-x-2.5 overflow-x-auto">
          <span className="text-xs text-[#786F66] font-bold mr-1 uppercase tracking-wider">Category:</span>
          {categories.map((cat) => (
            <button
              key={cat}
              onClick={() => setSelectedCategory(cat)}
              className={`px-3 py-1.5 text-xs font-extrabold uppercase tracking-wider rounded-lg transition-colors ${
                selectedCategory === cat
                  ? 'bg-[#2B2523] text-white shadow-xs'
                  : 'text-[#574E46] hover:bg-[#F5F1EB]'
              }`}
            >
              {cat}
            </button>
          ))}
        </div>

        <span className="text-xs text-[#786F66] font-semibold">
          Showing {filteredRequirements.length} of {requirements.length} conditions
        </span>
      </div>

      {/* STRIPPED-DOWN CHECKLIST TABLE */}
      <div className="border border-[#E5E0DA] bg-white rounded-2xl overflow-hidden shadow-xs">
        <table className="w-full text-left border-collapse">
          <thead>
            <tr className="border-b border-[#E5E0DA] text-xs font-extrabold uppercase tracking-wider text-[#574E46]">
              <th className="py-4 px-6 w-[50px] text-center">#</th>
              <th className="py-4 px-6">Requirement Name</th>
              <th className="py-4 px-6">Extraction category</th>
              <th className="py-4 px-6">Source Reference</th>
              <th className="py-4 px-6">Category</th>
              <th className="py-4 px-6 text-right">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-[#E5E0DA] text-sm">
            {filteredRequirements.length === 0 ? (
              <tr>
                <td colSpan={6} className="text-center py-12 text-[#786F66] text-sm">
                  No requirements found in category "{selectedCategory}".
                </td>
              </tr>
            ) : (
              filteredRequirements.map((req, idx) => (
                <tr key={req.requirement_id} className="hover:bg-[#FAF8F5] transition-colors">
                  <td className="py-4 px-6 text-center font-mono font-bold text-[#786F66] text-sm">
                    {idx + 1}
                  </td>

                  <td className="py-4 px-6 font-bold text-[#2B2523] text-base">
                    {req.name} <span className="text-xs font-mono font-semibold text-[#786F66]">({req.requirement_id})</span>
                  </td>

                  <td className="py-4 px-6 font-extrabold text-sm text-[#B3432E]">
                    {formatCondition(req)}
                  </td>

                  <td className="py-4 px-6 text-[#574E46] font-semibold text-sm">
                    Clause <strong className="text-[#2B2523]">{req.source.clause}</strong> • Page {req.source.page}
                  </td>

                  <td className="py-4 px-6 text-xs font-extrabold uppercase tracking-wider text-[#574E46]">
                    {req.category}
                  </td>

                  <td className="py-4 px-6 text-right">
                    <div className="flex items-center justify-end space-x-3">
                      <button
                        disabled={isApproved}
                        onClick={() => handleOpenEdit(req)}
                        className="text-[#786F66] hover:text-[#B3432E] disabled:opacity-30 p-1"
                        title="Edit"
                      >
                        <Edit3 className="w-4 h-4" />
                      </button>

                      <button
                        disabled={isApproved}
                        onClick={() => handleOpenDelete(req.requirement_id)}
                        className="text-[#786F66] hover:text-red-700 disabled:opacity-30 p-1"
                        title="Delete"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>

        {/* Bottom Add Action Row */}
        <div className="p-4 bg-[#FAF8F5] border-t border-[#E5E0DA] flex items-center justify-between">
          <button
            onClick={handleOpenAdd}
            disabled={isApproved}
            className="border border-[#E5E0DA] bg-white text-[#2B2523] hover:bg-[#F5F1EB] disabled:opacity-40 px-4 py-2 rounded-xl text-sm font-semibold flex items-center space-x-2 transition-colors"
          >
            <Plus className="w-4 h-4 text-[#B3432E]" />
            <span>Add Condition</span>
          </button>

          <span className="text-xs text-[#786F66] font-medium">
            {isApproved ? 'Checklist approved and locked' : 'Click + to add a missed clause'}
          </span>
        </div>
      </div>

      {/* ADD DIALOG */}
      {isAddOpen && (
        <div className="fixed inset-0 z-50 bg-black/40 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white border border-[#E5E0DA] rounded-2xl p-8 max-w-lg w-full space-y-4 shadow-2xl">
            <h3 className="text-lg font-extrabold text-[#2B2523]">Add Eligibility Requirement</h3>

            <form onSubmit={handleSaveAdd} className="space-y-4 py-1 text-sm">
              <div>
                <label className="font-bold text-[#2B2523] block mb-1">Requirement Name</label>
                <input
                  required
                  placeholder="e.g. Local Content Percentage"
                  value={formName}
                  onChange={(e) => setFormName(e.target.value)}
                  className="w-full px-4 py-2 border border-[#E5E0DA] rounded-xl focus:outline-none focus:border-[#B3432E]"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="font-bold text-[#2B2523] block mb-1">Category</label>
                  <select 
                    value={formCategory} 
                    onChange={(e) => setFormCategory(e.target.value)}
                    className="w-full px-3 py-2 border border-[#E5E0DA] rounded-xl focus:outline-none"
                  >
                    {categories.filter(c => c !== 'ALL').map(c => (
                      <option key={c} value={c}>{c}</option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="font-bold text-[#2B2523] block mb-1">Operator</label>
                  <select 
                    value={formOperator} 
                    onChange={(e) => setFormOperator(e.target.value)}
                    className="w-full px-3 py-2 border border-[#E5E0DA] rounded-xl focus:outline-none"
                  >
                    <option value=">=">&gt;= (At least)</option>
                    <option value="<=">&lt;= (Maximum)</option>
                    <option value="==">== (Exact match)</option>
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="font-bold text-[#2B2523] block mb-1">Required Value</label>
                  <input
                    required
                    placeholder="e.g. 50"
                    value={formValue}
                    onChange={(e) => setFormValue(e.target.value)}
                    className="w-full px-4 py-2 border border-[#E5E0DA] rounded-xl focus:outline-none focus:border-[#B3432E]"
                  />
                </div>

                <div>
                  <label className="font-bold text-[#2B2523] block mb-1">Unit</label>
                  <input
                    placeholder="e.g. %, Cr, Years"
                    value={formUnit}
                    onChange={(e) => setFormUnit(e.target.value)}
                    className="w-full px-4 py-2 border border-[#E5E0DA] rounded-xl focus:outline-none focus:border-[#B3432E]"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="font-bold text-[#2B2523] block mb-1">Clause Ref</label>
                  <input
                    placeholder="e.g. 8.2"
                    value={formClause}
                    onChange={(e) => setFormClause(e.target.value)}
                    className="w-full px-4 py-2 border border-[#E5E0DA] rounded-xl focus:outline-none focus:border-[#B3432E]"
                  />
                </div>

                <div>
                  <label className="font-bold text-[#2B2523] block mb-1">Page Number</label>
                  <input
                    type="number"
                    placeholder="e.g. 14"
                    value={formPage}
                    onChange={(e) => setFormPage(e.target.value)}
                    className="w-full px-4 py-2 border border-[#E5E0DA] rounded-xl focus:outline-none focus:border-[#B3432E]"
                  />
                </div>
              </div>

              <div className="flex justify-end space-x-3 pt-4">
                <button 
                  type="button" 
                  onClick={() => setIsAddOpen(false)}
                  className="px-4 py-2 border border-[#E5E0DA] text-[#574E46] rounded-xl text-sm font-semibold"
                >
                  Cancel
                </button>
                <button 
                  type="submit" 
                  className="px-5 py-2 bg-[#B3432E] text-white rounded-xl text-sm font-extrabold"
                >
                  Save Requirement
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* EDIT DIALOG */}
      {isEditOpen && (
        <div className="fixed inset-0 z-50 bg-black/40 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white border border-[#E5E0DA] rounded-2xl p-8 max-w-lg w-full space-y-4 shadow-2xl">
            <h3 className="text-lg font-extrabold text-[#2B2523]">Edit Requirement Rule</h3>

            <form onSubmit={handleSaveEdit} className="space-y-4 py-1 text-sm">
              <div>
                <label className="font-bold text-[#2B2523] block mb-1">Requirement Name</label>
                <input
                  required
                  value={formName}
                  onChange={(e) => setFormName(e.target.value)}
                  className="w-full px-4 py-2 border border-[#E5E0DA] rounded-xl focus:outline-none focus:border-[#B3432E]"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="font-bold text-[#2B2523] block mb-1">Category</label>
                  <select 
                    value={formCategory} 
                    onChange={(e) => setFormCategory(e.target.value)}
                    className="w-full px-3 py-2 border border-[#E5E0DA] rounded-xl focus:outline-none"
                  >
                    {categories.filter(c => c !== 'ALL').map(c => (
                      <option key={c} value={c}>{c}</option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="font-bold text-[#2B2523] block mb-1">Operator</label>
                  <select 
                    value={formOperator} 
                    onChange={(e) => setFormOperator(e.target.value)}
                    className="w-full px-3 py-2 border border-[#E5E0DA] rounded-xl focus:outline-none"
                  >
                    <option value=">=">&gt;= (At least)</option>
                    <option value="<=">&lt;= (Maximum)</option>
                    <option value="==">== (Exact match)</option>
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="font-bold text-[#2B2523] block mb-1">Required Value</label>
                  <input
                    required
                    value={formValue}
                    onChange={(e) => setFormValue(e.target.value)}
                    className="w-full px-4 py-2 border border-[#E5E0DA] rounded-xl focus:outline-none focus:border-[#B3432E]"
                  />
                </div>

                <div>
                  <label className="font-bold text-[#2B2523] block mb-1">Unit</label>
                  <input
                    value={formUnit}
                    onChange={(e) => setFormUnit(e.target.value)}
                    className="w-full px-4 py-2 border border-[#E5E0DA] rounded-xl focus:outline-none focus:border-[#B3432E]"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="font-bold text-[#2B2523] block mb-1">Clause Ref</label>
                  <input
                    value={formClause}
                    onChange={(e) => setFormClause(e.target.value)}
                    className="w-full px-4 py-2 border border-[#E5E0DA] rounded-xl focus:outline-none focus:border-[#B3432E]"
                  />
                </div>

                <div>
                  <label className="font-bold text-[#2B2523] block mb-1">Page Number</label>
                  <input
                    type="number"
                    value={formPage}
                    onChange={(e) => setFormPage(e.target.value)}
                    className="w-full px-4 py-2 border border-[#E5E0DA] rounded-xl focus:outline-none focus:border-[#B3432E]"
                  />
                </div>
              </div>

              <div className="flex justify-end space-x-3 pt-4">
                <button 
                  type="button" 
                  onClick={() => setIsEditOpen(false)}
                  className="px-4 py-2 border border-[#E5E0DA] text-[#574E46] rounded-xl text-sm font-semibold"
                >
                  Cancel
                </button>
                <button 
                  type="submit" 
                  className="px-5 py-2 bg-[#B3432E] text-white rounded-xl text-sm font-extrabold"
                >
                  Update Requirement
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* DELETE DIALOG */}
      {isDeleteOpen && (
        <div className="fixed inset-0 z-50 bg-black/40 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white border border-[#E5E0DA] rounded-2xl p-6 max-w-md w-full space-y-4 shadow-2xl">
            <h3 className="text-lg font-extrabold text-red-700">Delete Requirement</h3>
            <p className="text-sm text-[#786F66] leading-relaxed font-medium">
              Are you sure you want to remove this requirement from the checklist?
            </p>

            <div className="flex justify-end space-x-3 pt-2">
              <button 
                onClick={() => setIsDeleteOpen(false)}
                className="px-4 py-2 border border-[#E5E0DA] text-[#574E46] rounded-xl text-sm font-semibold"
              >
                Cancel
              </button>
              <button 
                onClick={handleConfirmDelete}
                className="px-5 py-2 bg-red-700 text-white rounded-xl text-sm font-extrabold"
              >
                Delete
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
