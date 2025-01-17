//    |  /           |
//    ' /   __| _` | __|  _ \   __|
//    . \  |   (   | |   (   |\__ `
//   _|\_\_|  \__,_|\__|\___/ ____/
//                   Multi-Physics
//
//  License:         BSD License
//                   Kratos default license: kratos/license.txt
//
//  Main authors:    Pooyan Dadvand
//                  

#pragma once

// System includes

// External includes

// Project includes
#include "includes/define.h"

namespace Kratos
{
///@addtogroup KratosCore
///@{

///@name Kratos Classes
///@{

/**
 * @brief Representing a bounding box by storing the min and max points
 * @details It stores the min and max points and have constructor for it construction with any container of points.
 *  TPointType should provide access operator [] to its coordinate and deep copy operator=
 * @tparam TPointType The type of point considered
 * @author Pooyan Dadvand
 */
template <typename TPointType>
class BoundingBox 
{
public:
    ///@name Type Definitions
    ///@{

    /// Pointer definition of BoundingBox
    KRATOS_CLASS_POINTER_DEFINITION(BoundingBox);

    ///@}
    ///@name Life Cycle
    ///@{

    /// Default constructor
    BoundingBox()
    {
        std::fill(GetMinPoint().begin(), GetMinPoint().end(), 0.0);
        std::fill(GetMaxPoint().begin(), GetMaxPoint().end(), 0.0);
    };

    BoundingBox(TPointType const& MinPoint, TPointType const& MaxPoint) :
		mMinMaxPoints{MinPoint,MaxPoint} {}

    /// Copy constructor
    BoundingBox( const BoundingBox &Other) :
		mMinMaxPoints(Other.mMinMaxPoints) {}


    /// Construction with container of points.
    template<typename TIteratorType>
    BoundingBox(TIteratorType const& PointsBegin, TIteratorType const& PointsEnd) 
    {
        Set(PointsBegin, PointsEnd);
    }

    /// Destructor.
    virtual ~BoundingBox(){}

    ///@}
    ///@name Operators
    ///@{

    /// Assignment operator.
    BoundingBox& operator=(BoundingBox const& rOther)
    {
        GetMinPoint() = rOther.GetMinPoint();
        GetMaxPoint() = rOther.GetMaxPoint();

        return *this;
    }

    ///@}
    ///@name Operations
    ///@{

    template<typename TIteratorType>
    void Set(TIteratorType const& PointsBegin, TIteratorType const& PointsEnd)
    {
        if (PointsBegin == PointsEnd) {
            std::fill(GetMinPoint().begin(), GetMinPoint().end(), 0.0);
            std::fill(GetMaxPoint().begin(), GetMaxPoint().end(), 0.0);
            return;
        }

        for (unsigned int i = 0; i < Dimension; i++) {
            GetMinPoint()[i] = (*PointsBegin)[i];
            GetMaxPoint()[i] = (*PointsBegin)[i];
        }

        Extend(PointsBegin, PointsEnd);
    }

    template<typename TIteratorType>
    void Extend(TIteratorType const& PointsBegin, TIteratorType const& PointsEnd)
    {
        for (TIteratorType i_point = PointsBegin; i_point != PointsEnd; i_point++){
            for (unsigned int i = 0; i < Dimension; i++) {
                if ((*i_point)[i] < GetMinPoint()[i]) GetMinPoint()[i] = (*i_point)[i];
                if ((*i_point)[i] > GetMaxPoint()[i]) GetMaxPoint()[i] = (*i_point)[i];
            }
        }
    }

    void Extend(const double Margin)
    {
        for (unsigned int i = 0; i < Dimension; i++){
            GetMinPoint()[i] -= Margin;
            GetMaxPoint()[i] += Margin;
        }

    }

    ///@}
    ///@name Access
    ///@{

    TPointType& GetMinPoint() { return mMinMaxPoints[0]; }
    
    TPointType const& GetMinPoint() const { return mMinMaxPoints[0]; }

    TPointType& GetMaxPoint() { return mMinMaxPoints[1]; }
    
    TPointType const& GetMaxPoint() const { return mMinMaxPoints[1]; }

    ///@}
    ///@name Inquiry
    ///@{

    ///@}
    ///@name Input and output
    ///@{

    /// Turn back information as a string.
    virtual std::string Info() const
    {
        std::stringstream buffer;
        buffer << "BoundingBox" ;
        return buffer.str();
    }

    /// Print information about this object.
    virtual void PrintInfo(std::ostream& rOStream) const {rOStream << "BoundingBox";}

    /// Print object's data.
    virtual void PrintData(std::ostream& rOStream) const {
        rOStream << "   MinPoint : [" << GetMinPoint()[0] << ","  << GetMinPoint()[1] << ","  << GetMinPoint()[2] << "]" << std::endl;
        rOStream << "   MaxPoint : [" << GetMaxPoint()[0] << ","  << GetMaxPoint()[1] << ","  << GetMaxPoint()[2] << "]" << std::endl;
    }

    ///@}
    ///@name Friends
    ///@{

    ///@}
private:
    ///@name Static Member Variables
    ///@{
    
    static constexpr unsigned int Dimension = 3;
    
    ///@}
    ///@name Member Variables
    ///@{

    std::array<TPointType, 2> mMinMaxPoints;  /// The min and max points 

    ///@}

}; // Class BoundingBox

///@}
///@name Type Definitions
///@{

///@}
///@name Input and output
///@{

/// input stream function
template <typename TPointType>
inline std::istream& operator >> (std::istream& rIStream,
                BoundingBox<TPointType>& rThis){
                    return rIStream;
                }

/// output stream function
template <typename TPointType>
inline std::ostream& operator << (std::ostream& rOStream,
                const BoundingBox<TPointType>& rThis)
{
    rThis.PrintInfo(rOStream);
    rOStream << std::endl;
    rThis.PrintData(rOStream);

    return rOStream;
}
///@}

///@} addtogroup block

}  // namespace Kratos.
