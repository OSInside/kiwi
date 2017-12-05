<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
<xsl:output method="xml"
        indent="yes" omit-xml-declaration="no" encoding="utf-8"/>

<!-- default rule -->
<xsl:template match="*" mode="conv39to41">
        <xsl:copy>
                <xsl:copy-of select="@*"/>
                     <xsl:apply-templates mode="conv39to41"/>
        </xsl:copy>  
</xsl:template>

<!-- version update -->
<para xmlns="http://docbook.org/ns/docbook">
        Changed attribute <tag class="attribute">schemaversion</tag>
        to <tag class="attribute">schemaversion</tag> from
        <literal>3.9</literal> to <literal>4.1</literal>. Adding
        <tag class="attribute">image</tag> attribute to
        <tag class="element">type</tag> element and collecting the
        appropriate <tag class="element">*config</tag> elements as
        children of the <tag class="element">type</tag> element.
</para>
<xsl:template match="image" mode="conv39to41">
    <xsl:choose>
        <!-- nothing to do if already at 4.1 -->
        <xsl:when test="@schemaversion > 3.9">
            <xsl:copy-of select="/"/>
        </xsl:when>
        <!-- otherwise apply templates -->
        <xsl:otherwise>
            <image schemaversion="4.1">
                <xsl:copy-of select="@*[local-name() != 'schemaversion']"/>
                <xsl:apply-templates  mode="conv39to41"/>  
            </image>
        </xsl:otherwise>
    </xsl:choose>
</xsl:template>

<xsl:template match="preferences" mode="conv39to41">
    <preferences>
            <xsl:copy-of select="@*"/>
            <xsl:apply-templates mode="conv39to41"/>
    </preferences>
</xsl:template>

<!-- modify the type element -->
<xsl:template match="type" mode="conv39to41">
        <xsl:choose>
                <xsl:when test="text()='ec2'">
                        <type>
                                <xsl:call-template name="insertcomprops"/>
                        </type>
                </xsl:when>
                <xsl:when test="text()='iso'">
                        <type>
                                <xsl:call-template name="insertcomprops"/>
                <xsl:call-template name="insertvmconfig"/>
                <xsl:call-template name="insertxenconfig"/>
                        </type>
                </xsl:when>
                <xsl:when test="text()='oem'">
                        <type>
                                <xsl:call-template name="insertcomprops"/>
                                <xsl:call-template name="insertlvm"/>
                                <xsl:call-template name="insertoemconfig"/>
                                <xsl:call-template name="insertvmconfig"/>
                                <xsl:call-template name="insertxenconfig"/>
                        </type>
                </xsl:when>
                <xsl:when test="text()='split'">
                        <type>
                                <xsl:call-template name="insertcomprops"/>
                                <xsl:call-template name="insertoemconfig"/>
                                <xsl:call-template name="insertsplit"/>
                                <xsl:call-template name="insertvmconfig"/>
                                <xsl:call-template name="insertxenconfig"/>
                        </type>
                </xsl:when>
                <xsl:when test="text()='usb'">
                        <type>
                                <xsl:call-template name="insertcomprops"/>
                                <xsl:call-template name="insertlvm"/>
                        </type>
                </xsl:when>
                <xsl:when test="text()='vmx'">
                        <type>
                                <xsl:call-template name="insertcomprops"/>
                                <xsl:call-template name="insertlvm"/>
                                <xsl:call-template name="insertvmconfig"/>
                                <xsl:call-template name="insertxenconfig"/>
                        </type>
                </xsl:when>
                <xsl:when test="text()='xen'">
                        <type>
                                <xsl:call-template name="insertcomprops"/>
                                <xsl:call-template name="insertxenconfig"/>
                        </type>
                </xsl:when>
                <xsl:when test="text()='pxe'">
                        <type>
                                <xsl:call-template name="insertcomprops"/>
                                <xsl:call-template name="insertpxe"/>
                        </type>
                </xsl:when>
                <xsl:otherwise>
                        <type>
                                <xsl:call-template name="insertcomprops" />
                                <xsl:apply-templates select="*"/>
                        </type>
                </xsl:otherwise>
        </xsl:choose>
</xsl:template>

<!-- generic insertion of block children -->
<xsl:template name="insertblockchldnodes" mode="conv39to41">
        <xsl:param name="blockname"/>
        <xsl:for-each select="$blockname/*">
                <xsl:copy-of select="current()"/>
        </xsl:for-each>
</xsl:template>

<!-- add properties common to all type elements -->
<xsl:template name="insertcomprops" mode="conv39to41">
        <xsl:attribute name="image">
                <xsl:value-of select="current()"/>
        </xsl:attribute>
        <xsl:copy-of select="@*"/>
        <xsl:if test="/image/preferences/size">
                <xsl:copy-of select="/image/preferences/size"/>
        </xsl:if>
</xsl:template>

<!-- insert the lvmvolumes block -->
<xsl:template name="insertlvm" mode="conv39to41">
        <xsl:if test="/image/lvmvolumes">
                <lvmvolumes>
                <xsl:call-template name="insertblockchldnodes">
                        <xsl:with-param name="blockname" select="/image/lvmvolumes"/>
                </xsl:call-template>
                </lvmvolumes>
        </xsl:if>
</xsl:template>

<!-- insert the oemconfig block -->
<xsl:template name="insertoemconfig" mode="conv39to41">
        <xsl:if test="/image/oemconfig">
                <oemconfig>
                <xsl:call-template name="insertblockchldnodes">
                    <xsl:with-param name="blockname" select="/image/oemconfig"/>
                </xsl:call-template>
                </oemconfig>
        </xsl:if>
</xsl:template>

<!-- insert the pxedeploy block -->
<xsl:template name="insertpxe" mode="conv39to41">
        <xsl:if test="/image/pxedeploy">
                <pxedeploy>
                <xsl:copy-of select="/image/pxedeploy/@*"/>
                <xsl:call-template name="insertblockchldnodes">
                        <xsl:with-param name="blockname" select="/image/pxedeploy"/>
                </xsl:call-template>  
                </pxedeploy>
        </xsl:if>
</xsl:template>

<!-- insert the split block -->
<xsl:template name="insertsplit" mode="conv39to41">
        <xsl:if test="/image/split">
                <split>
                <xsl:call-template name="insertblockchldnodes">
                        <xsl:with-param name="blockname" select="/image/split"/>
                </xsl:call-template>
                </split>
        </xsl:if>
</xsl:template>

<!-- Insert the vmwareconfig block -->
<xsl:template name="insertvmconfig" mode="conv39to41">
        <xsl:if test="/image/vmwareconfig">
                <vmwareconfig>
                <xsl:copy-of select="/image/vmwareconfig/@*"/>
                <xsl:call-template name="insertblockchldnodes">
                        <xsl:with-param name="blockname" select="/image/vmwareconfig"/>
                </xsl:call-template>
                </vmwareconfig>
        </xsl:if>
</xsl:template>

<!-- Insert the xenconfig block -->
<xsl:template name="insertxenconfig" mode="conv39to41">
        <xsl:if test="/image/xenconfig">
                <xenconfig>
                <xsl:copy-of select="/image/xenconfig/@*"/>
                <xsl:call-template name="insertblockchldnodes">
                        <xsl:with-param name="blockname" select="/image/xenconfig"/>
                </xsl:call-template>
                </xenconfig>
        </xsl:if>
</xsl:template>

<!-- Do not emmit blocks that have moved -->
<xsl:template match="lvmvolumes" mode="conv39to41"/>
<xsl:template match="oemconfig" mode="conv39to41"/>
<xsl:template match="pxedeploy" mode="conv39to41"/>
<xsl:template match="size" mode="conv39to41"/>
<xsl:template match="split" mode="conv39to41"/>
<xsl:template match="vmwareconfig" mode="conv39to41"/>
<xsl:template match="xenconfig" mode="conv39to41"/>

</xsl:stylesheet>
